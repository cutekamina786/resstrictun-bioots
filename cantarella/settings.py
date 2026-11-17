import os
from pyrogram import Client, filters, enums
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from database.db import db
from cantarella.strings import COMMANDS_TXT
from config import OWNER_ID
from cantarella.targetchat import (
    parse_target_input, inspect_target, format_report, forget_preflight, esc
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
# /setchat - Set / Check / Clear the target chat (channel or group)
# ======================================================
@Client.on_message(filters.command("setchat") & filters.private)
async def set_dump_chat(client: Client, message: Message):
    user_id = message.from_user.id
    if not await db.is_user_exist(user_id):
        await db.add_user(user_id, message.from_user.first_name)
    current = await db.get_dump_chat(user_id)
    if len(message.command) < 2:
        text = (
            "<b>🎯 Set Target Chat</b>\n\n"
            "<b>Usage:</b>\n"
            "<code>/setchat -1001234567890</code> → chat ID\n"
            "<code>/setchat @mychannel</code> → public @username\n"
            "<code>/setchat check</code> → re-check your current target\n"
            "<code>/setchat clear</code> → turn it off\n\n"
            "<b>Requirements:</b>\n"
            "• The bot must be added to the channel/group (admin with <i>Post Messages</i> for channels)\n"
            "• You must be an admin/owner of that chat\n\n"
            "<i>Once set, every link you send is forwarded into that chat. "
            "Progress, completion and errors are shown here in the bot.</i>\n\n"
        )
        text += (f"<b>Current target:</b> <code>{current}</code>" if current else "<b>Current target:</b> not set")
        return await message.reply_text(text, parse_mode=enums.ParseMode.HTML)
    arg = " ".join(message.command[1:]).strip()
    low = arg.lower()
    if low in ("clear", "remove", "off", "reset", "none", "delete"):
        await db.set_dump_chat(user_id, None)
        forget_preflight(current)
        return await message.reply_text(
            "✅ <b>Target Chat Cleared</b>\n\n<i>Saved content will now be sent to this bot chat again.</i>",
            parse_mode=enums.ParseMode.HTML
        )
    if low in ("check", "status", "test"):
        if not current:
            return await message.reply_text("ℹ️ <b>No target chat is set.</b>\n<i>Use /setchat &lt;chat_id&gt;</i>", parse_mode=enums.ParseMode.HTML)
        wait = await message.reply_text("🔎 <i>Checking your target chat...</i>", parse_mode=enums.ParseMode.HTML)
        forget_preflight(current)
        rep = await inspect_target(client, [current], user_id=user_id, owner_id=OWNER_ID, send_test=True)
        text = format_report(rep, saved=None)
        if not rep["ok"]:
            text += "\n\n<i>Fix the problem above, or use /setchat clear.</i>"
        return await wait.edit_text(text, parse_mode=enums.ParseMode.HTML)
    candidates, err = parse_target_input(arg)
    if err:
        return await message.reply_text(f"❌ <b>Invalid Chat</b>\n\n<i>{esc(err)}</i>", parse_mode=enums.ParseMode.HTML)
    wait = await message.reply_text("🔎 <i>Verifying the chat, the bot's admin rights and your rights...</i>", parse_mode=enums.ParseMode.HTML)
    try:
        rep = await inspect_target(client, candidates, user_id=user_id, owner_id=OWNER_ID, send_test=True)
        if rep["ok"]:
            await db.set_dump_chat(user_id, rep["chat_id"])
            forget_preflight(rep["chat_id"])
        await wait.edit_text(format_report(rep, saved=rep["ok"]), parse_mode=enums.ParseMode.HTML)
    except Exception as e:
        await wait.edit_text(f"❌ <b>Unable to check this chat</b>\n<code>{esc(e)}</code>", parse_mode=enums.ParseMode.HTML)
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
            rep = await inspect_target(client, [current], user_id=user_id, owner_id=OWNER_ID, send_test=False)
            text = format_report(rep, saved=None)
            text += "\n\n<i>All saved content is forwarded to this chat. Use /setchat to change, /setchat check to test, /setchat clear to remove.</i>"
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
