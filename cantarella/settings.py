import os
from pyrogram import Client, filters, enums
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from database.db import db
from cantarella.strings import COMMANDS_TXT
from config import OWNER_ID
from cantarella.targetchat import (
    parse_target_input, inspect_target, format_report, forget_preflight, esc,
    check_user_target, forget_user_preflight, format_dual_report, mode_label,
    fwd_buttons, FWD_ASK, FWD_EXPLAIN, pending_forward
)
# ======================================================
# /settings - Enhanced Professional Settings Menu
# ======================================================
@Client.on_message(filters.command("settings") & filters.private)
async def settings_menu(client: Client, message: Message):
    user_id = message.from_user.id
    # Ensure user exists (Safe Call)
    if not await db.is_user_exist(user_id):
        await db.add_user(user_id, message.from_user.first_name)
    # Fetch real status
    is_premium = await db.check_premium(user_id)
    premium_badge = "💎 Premium Member" if is_premium else "👤 Free User"
    buttons = InlineKeyboardMarkup([
        [InlineKeyboardButton("📜 Commands List", callback_data="cmd_list_btn")],
        [InlineKeyboardButton("📊 My Usage Stats", callback_data="user_stats_btn")],
        [InlineKeyboardButton("🗑 Dump Chat", callback_data="dump_chat_btn")],
        [
            InlineKeyboardButton("🖼 Thumbnail", callback_data="thumb_btn"),
            InlineKeyboardButton("📝 Caption", callback_data="caption_btn")
        ],
        [InlineKeyboardButton("❌ Close Menu", callback_data="close_btn")]
    ])
    text = (
        f"<b>⚙️ Settings Panel</b>\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"<b>Account:</b> {premium_badge}\n"
        f"<b>User ID:</b> <code>{user_id}</code>\n\n"
        f"<i>Select an option below to customize your experience.</i>"
    )
    await message.reply_text(text, reply_markup=buttons, parse_mode=enums.ParseMode.HTML)
# ======================================================
# /commands - Direct Access to Commands List
# ======================================================
@Client.on_message(filters.command("commands") & filters.private)
async def direct_commands(client: Client, message: Message):
    buttons = InlineKeyboardMarkup([
        [InlineKeyboardButton("⚙️ Open Settings", callback_data="settings_back_btn"), InlineKeyboardButton("❌ Close", callback_data="close_btn")]
    ])
    await message.reply_text(
        COMMANDS_TXT,
        reply_markup=buttons,
        parse_mode=enums.ParseMode.HTML,
        disable_web_page_preview=True
    )
# ======================================================
# Helpers: check BOTH ways of forwarding (As Bot / As User)
# ======================================================
async def gather_reports(client, user_id, candidates, send_test=True):
    bot_rep = await inspect_target(client, candidates, user_id=user_id, owner_id=OWNER_ID, send_test=send_test)
    session = await db.get_session(user_id)
    user_rep = None
    if session:
        cands = [bot_rep["chat_id"]] if bot_rep.get("chat_id") is not None else candidates
        user_rep = await check_user_target(session, cands)
    return bot_rep, user_rep, bool(session)
# ======================================================
# /setchat - Set / Check / Clear the target chat (channel or group)
# ======================================================
@Client.on_message(filters.command("setchat") & filters.private)
async def set_dump_chat(client: Client, message: Message):
    user_id = message.from_user.id
    if not await db.is_user_exist(user_id):
        await db.add_user(user_id, message.from_user.first_name)
    current = await db.get_dump_chat(user_id)
    if len(message.command) < 2:
        mode = await db.get_forward_mode(user_id)
        text = (
            "<b>🎯 Set Target Chat</b>\n\n"
            "<b>Usage:</b>\n"
            "<code>/setchat -1001234567890</code> → chat ID\n"
            "<code>/setchat @mychannel</code> → public @username\n"
            "<code>/setchat check</code> → re-check your current target\n"
            "<code>/setchat clear</code> → turn it off\n\n"
            "<b>Requirements:</b>\n"
            "• <b>As Bot:</b> the bot must be an admin of the channel/group (Post Messages)\n"
            "• <b>As User:</b> you must be logged in (/login) and be an admin there (Post Messages)\n\n"
            "<i>Once set, every link you send is forwarded into that chat. "
            "Progress, completion and errors are shown here in the bot. "
            "Choose As Bot / As User with /setforwarding.</i>\n\n"
        )
        text += (f"<b>Current target:</b> <code>{current}</code>\n" if current else "<b>Current target:</b> not set\n")
        text += f"<b>Forwarding mode:</b> {mode_label(mode)}"
        return await message.reply_text(text, parse_mode=enums.ParseMode.HTML)
    arg = " ".join(message.command[1:]).strip()
    low = arg.lower()
    if low in ("clear", "remove", "off", "reset", "none", "delete"):
        await db.set_dump_chat(user_id, None)
        forget_preflight(current)
        forget_user_preflight(user_id)
        return await message.reply_text(
            "✅ <b>Target Chat Cleared</b>\n\n<i>Saved content will now be sent to this bot chat again.</i>",
            parse_mode=enums.ParseMode.HTML
        )
    if low in ("check", "status", "test"):
        if not current:
            return await message.reply_text("ℹ️ <b>No target chat is set.</b>\n<i>Use /setchat &lt;chat_id&gt;</i>", parse_mode=enums.ParseMode.HTML)
        wait = await message.reply_text("🔎 <i>Checking your target chat...</i>", parse_mode=enums.ParseMode.HTML)
        forget_preflight(current)
        forget_user_preflight(user_id)
        bot_rep, user_rep, logged_in = await gather_reports(client, user_id, [current], send_test=True)
        mode = await db.get_forward_mode(user_id)
        return await wait.edit_text(format_dual_report(bot_rep, user_rep, logged_in, saved=None, mode=mode), parse_mode=enums.ParseMode.HTML)
    candidates, err = parse_target_input(arg)
    if err:
        return await message.reply_text(f"❌ <b>Invalid Chat</b>\n\n<i>{esc(err)}</i>", parse_mode=enums.ParseMode.HTML)
    wait = await message.reply_text("🔎 <i>Verifying the chat, the bot's admin rights and your admin rights...</i>", parse_mode=enums.ParseMode.HTML)
    try:
        bot_rep, user_rep, logged_in = await gather_reports(client, user_id, candidates, send_test=True)
        mode = await db.get_forward_mode(user_id)
        user_ok = bool(user_rep and user_rep.get("ok"))
        chat_id = None
        if bot_rep["ok"]:
            chat_id = bot_rep["chat_id"]
        elif user_ok:
            chat_id = user_rep["chat_id"]
        if chat_id is not None:
            await db.set_dump_chat(user_id, chat_id)
            forget_preflight(chat_id)
            forget_user_preflight(user_id)
        await wait.edit_text(format_dual_report(bot_rep, user_rep, logged_in, saved=chat_id is not None, mode=mode), parse_mode=enums.ParseMode.HTML)
    except Exception as e:
        await wait.edit_text(f"❌ <b>Unable to check this chat</b>\n<code>{esc(e)}</code>", parse_mode=enums.ParseMode.HTML)
# ======================================================
# /setforwarding - choose As Bot / As User (saved globally)
# ======================================================
@Client.on_message(filters.command("setforwarding") & filters.private)
async def set_forwarding(client: Client, message: Message):
    user_id = message.from_user.id
    if not await db.is_user_exist(user_id):
        await db.add_user(user_id, message.from_user.first_name)
    mode = await db.get_forward_mode(user_id)
    if mode in ("bot", "user"):
        text = (
            "<b>⚙️ Forwarding Mode</b>\n"
            "━━━━━━━━━━━━━━━━━━\n"
            f"<b>Your set mode:</b> {mode_label(mode)}\n\n"
            "<i>You can change it by tapping a button below.</i>\n\n"
            + FWD_EXPLAIN
        )
    else:
        text = FWD_ASK
    if not await db.get_dump_chat(user_id):
        text += "\n\n<i>ℹ️ No target chat is set yet. Use /setchat &lt;chat_id&gt; first.</i>"
    await message.reply_text(text, reply_markup=fwd_buttons("fwds"), parse_mode=enums.ParseMode.HTML)
async def _edit_or_reply(cq, text, markup=None):
    try:
        await cq.edit_message_text(text, reply_markup=markup, parse_mode=enums.ParseMode.HTML)
    except Exception as e:
        if "MESSAGE_NOT_MODIFIED" in str(e).upper() or type(e).__name__ == "MessageNotModified":
            return
        try:
            await cq.message.reply_text(text, reply_markup=markup, parse_mode=enums.ParseMode.HTML)
        except Exception:
            pass
@Client.on_callback_query(filters.regex(r"^fwd[ps]_(bot|user)$"))
async def forwarding_mode_cb(client: Client, cq: CallbackQuery):
    user_id = cq.from_user.id
    prefix, mode = cq.data.split("_")
    from_prompt = prefix == "fwdp"      # tapped on the question that appeared after sending a link
    try:
        await cq.answer("Checking...")
    except Exception:
        pass
    dump = await db.get_dump_chat(user_id)
    problems = []
    if dump:
        if mode == "bot":
            rep = await inspect_target(client, [dump])
            problems = rep["problems"]
        else:
            session = await db.get_session(user_id)
            if not session:
                problems = ["You are not logged in. Send /login first, then choose As User."]
            else:
                rep = await check_user_target(session, [dump])
                problems = rep["problems"]
    if problems:
        text = (
            f"<b>❌ Cannot use {mode_label(mode)}</b>\n"
            "━━━━━━━━━━━━━━━━━━\n"
            + "\n".join(f"• <i>{esc(p)}</i>" for p in problems)
            + "\n\n<i>Fix it and tap again, or choose the other mode.</i>"
        )
        return await _edit_or_reply(cq, text, fwd_buttons(prefix))
    await db.set_forward_mode(user_id, mode)
    forget_preflight(dump)
    forget_user_preflight(user_id)
    text = (
        f"<b>✅ Forwarding mode saved: {mode_label(mode)}</b>\n\n"
        + ("<i>Content will be sent into your target chat by the bot.</i>" if mode == "bot"
           else "<i>Content will be sent into your target chat by your logged-in account.</i>")
        + "\n<i>Change it any time with /setforwarding.</i>"
    )
    if not dump:
        text += "\n\n<i>ℹ️ No target chat is set yet. Use /setchat &lt;chat_id&gt;.</i>"
    entry = pending_forward.pop(user_id, None) if from_prompt else None
    pending = entry["msgs"] if entry else []
    if pending:
        text += "\n\n<b>▶️ Starting your link now...</b>"
    elif from_prompt:
        text += "\n\n<i>Please send your link again to start.</i>"
    await _edit_or_reply(cq, text, None)
    if pending:
        from cantarella.start import save   # imported late: start.py is loaded after this file
        for pmsg in pending:
            try:
                await save(client, pmsg)
            except Exception as e:
                await cq.message.reply_text(f"❌ <b>Could not process the link</b>\n<code>{esc(e)}</code>", parse_mode=enums.ParseMode.HTML)
# ======================================================
# Callbacks - Full Settings Navigation
# ======================================================
@Client.on_callback_query(filters.regex("^(cmd_list_btn|dump_chat_btn|thumb_btn|caption_btn|user_stats_btn|settings_back_btn|close_btn)$"))
async def settings_callbacks(client: Client, callback_query: CallbackQuery):
    data = callback_query.data
    user_id = callback_query.from_user.id
   
    # Common back/close buttons
    back_close = [[InlineKeyboardButton("⬅️ Back", callback_data="settings_back_btn"), InlineKeyboardButton("❌ Close", callback_data="close_btn")]]
    if data == "cmd_list_btn":
        await callback_query.edit_message_text(
            COMMANDS_TXT,
            reply_markup=InlineKeyboardMarkup(back_close),
            parse_mode=enums.ParseMode.HTML,
            disable_web_page_preview=True
        )
    elif data == "dump_chat_btn":
        current = await db.get_dump_chat(user_id)
        if current:
            bot_rep, user_rep, logged_in = await gather_reports(client, user_id, [current], send_test=False)
            mode = await db.get_forward_mode(user_id)
            text = format_dual_report(bot_rep, user_rep, logged_in, saved=None, mode=mode)
            text += "\n\n<i>/setchat to change • /setchat check to test • /setforwarding to switch As Bot / As User • /setchat clear to remove.</i>"
        else:
            text = (
                "<b>🎯 No Target Chat Set</b>\n\n"
                "<i>Saved content appears only in this chat.</i>\n"
                "<i>Use /setchat &lt;chat_id&gt; to forward into a channel or group.</i>"
            )
        markup = InlineKeyboardMarkup(back_close)
        try:
            if callback_query.message.photo or callback_query.message.caption is not None:
                await callback_query.edit_message_caption(text, reply_markup=markup, parse_mode=enums.ParseMode.HTML)
            else:
                await callback_query.edit_message_text(text, reply_markup=markup, parse_mode=enums.ParseMode.HTML)
        except Exception:
            await callback_query.message.reply_text(text, reply_markup=markup, parse_mode=enums.ParseMode.HTML)
    elif data == "thumb_btn":
        thumb = await db.get_thumbnail(user_id)
        if thumb and os.path.exists(thumb):
            await callback_query.message.reply_photo(
                thumb,
                caption="<b>🖼 Your Current Custom Thumbnail</b>\n\n<i>Send a new photo to update • /del_thumb to remove</i>",
                parse_mode=enums.ParseMode.HTML
            )
            await callback_query.answer("Thumbnail preview sent below 👇")
        else:
            await callback_query.edit_message_text(
                "<b>🖼 No Custom Thumbnail Set</b>\n\n"
                "<i>Send a photo to set as default thumbnail for uploads.</i>",
                reply_markup=InlineKeyboardMarkup(back_close),
                parse_mode=enums.ParseMode.HTML
            )
    elif data == "caption_btn":
        caption = await db.get_caption(user_id)
        if caption:
            preview = caption.format(filename="Video_File_2024.mp4", size="1.2 GB")
            text = (
                f"<b>📝 Current Custom Caption</b>\n\n"
                f"<code>{caption}</code>\n\n"
                f"<b>Preview:</b>\n{preview}\n\n"
                "<i>Placeholders: {filename}, {size}</i>\n"
                "<i>/set_caption &lt;text&gt; to change • /del_caption to remove</i>"
            )
        else:
            text = (
                "<b>📝 No Custom Caption Set</b>\n\n"
                "<i>Use /set_caption &lt;text&gt; to set one.</i>\n"
                "<i>Supports {filename} and {size} placeholders.</i>"
            )
        await callback_query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(back_close), parse_mode=enums.ParseMode.HTML)
    elif data == "user_stats_btn":
        # Fetch real stats from DB
        is_premium = await db.check_premium(user_id)
        user_data = await db.col.find_one({'id': int(user_id)})
       
        if is_premium:
            limit_text = "♾️ Unlimited"
            usage_text = "Ignored (Premium)"
        else:
            # Free user logic
            daily_limit = 5
            used = user_data.get('daily_usage', 0)
            limit_text = f"{daily_limit} Files / 24h"
            usage_text = f"{used} / {daily_limit}"
        text = (
            f"<b>📊 My Usage Statistics</b>\n\n"
            f"<b>Plan:</b> {'💎 Premium' if is_premium else '👤 Free'}\n"
            f"<b>Daily Limit:</b> <code>{limit_text}</code>\n"
            f"<b>Today's Usage:</b> <code>{usage_text}</code>\n\n"
            f"<i>Upgrade to Premium for unlimited downloads!</i>"
        )
        await callback_query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(back_close), parse_mode=enums.ParseMode.HTML)
    elif data == "settings_back_btn":
        # Re-render main menu
        is_premium = await db.check_premium(user_id)
        premium_badge = "💎 Premium Member" if is_premium else "👤 Free User"
       
        buttons = InlineKeyboardMarkup([
            [InlineKeyboardButton("📜 Commands List", callback_data="cmd_list_btn")],
            [InlineKeyboardButton("📊 My Usage Stats", callback_data="user_stats_btn")],
            [InlineKeyboardButton("🗑 Dump Chat", callback_data="dump_chat_btn")],
            [
                InlineKeyboardButton("🖼 Thumbnail", callback_data="thumb_btn"),
                InlineKeyboardButton("📝 Caption", callback_data="caption_btn")
            ],
            [InlineKeyboardButton("❌ Close Menu", callback_data="close_btn")]
        ])
       
        text = (
            f"<b>⚙️ Settings Panel</b>\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"<b>Account:</b> {premium_badge}\n"
            f"<b>User ID:</b> <code>{user_id}</code>\n\n"
            f"<i>Select an option below to customize your experience.</i>"
        )
       
        await callback_query.edit_message_text(text, reply_markup=buttons, parse_mode=enums.ParseMode.HTML)
    elif data == "close_btn":
        await callback_query.message.delete()
    await callback_query.answer()
