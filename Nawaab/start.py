# Developed by: Vip Nawaab
# Telegram: Team Nawaab
import os
import re
import asyncio
import random
import time
import shutil
import pyrogram
import requests
import html as _html
from pyrogram import Client, filters, enums
from pyrogram.errors import (
    FloodWait, UserIsBlocked, InputUserDeactivated, UserAlreadyParticipant,
    InviteHashExpired, UsernameNotOccupied, AuthKeyUnregistered, UserDeactivated, UserDeactivatedBan
)
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message, CallbackQuery, InputMediaPhoto, ReplyKeyboardRemove
from config import API_ID, API_HASH, ERROR_MESSAGE, OWNER_USERNAME, OWNER_LINK, CHANNEL_NAME, CHANNEL_LINK
from database.db import db
from Nawaab.targetchat import (
    explain_error, dest_error_kind, preflight, user_preflight, pending_forward,
    fwd_buttons, FWD_ASK, mode_label
)
import math
from logger import LOGGER
logger = LOGGER(__name__)
SUBSCRIPTION = os.environ.get('SUBSCRIPTION', 'https://graph.org/file/242b7f1b52743938d81f1.jpg')
FREE_LIMIT_SIZE = 2 * 1024 * 1024 * 1024
FREE_LIMIT_DAILY = 5
REACTIONS = [
    "👍", "❤️", "🔥", "🥰", "👏", "😁", "🤔", "🤯", "😱",
    "😢", "🎉", "🤩", "🙏", "👌", "🕊",
    "🥴", "😍", "🐳", "❤️‍🔥", "🌚", "💯", "🤣", "⚡",
    "🏆", "💔", "🤨", "😐", "🍓", "🍾", "💋", "😈", "😴",
    "😭", "🤓", "👻", "👨‍💻", "👀", "🎃", "🙈", "😇", "😨", "🤝",
    "✍", "🤗", "🫡", "🎅", "🎄", "☃", "💅", "🤪", "🗿", "🆒",
    "💘", "🙉", "🦄", "😘", "💊", "🙊", "😎", "👾", "🤷‍♂️", "🤷‍♀️",
    "😡"
]


dev_text = f"👨‍💻 Mind Behind This Bot:\n• {OWNER_USERNAME}"
channels_text = f"📢 Official Channels:\n• {CHANNEL_NAME}\n\nStay updated for new features!"

class script(object):
   
    START_TXT = """<b>👋 Hello {},</b>
<b>🤖 I am <a href=https://t.me/{}>{}</a></b>
<i>Your Professional Restricted Content Saver Bot.</i>
<blockquote><b>🚀 System Status: 🟢 Online</b>
<b>⚡ Performance: 30x High-Speed Processing</b>
<b>🔐 Security: End-to-End Encrypted</b>
<b>📊 Uptime: 99.99% Guaranteed</b></blockquote>
<b>👇 Select an Option Below to Get Started:</b>
"""
    HELP_TXT = """<b>📚 Comprehensive Help & User Guide</b>
<blockquote><b>1️⃣ Public Channels (No Login Required)</b></blockquote>
• Forward or send the post link directly.
• Compatible with any public channel or group.
• <i>Example Link:</i> <code>https://t.me/channel/123</code>
<blockquote><b>2️⃣ Private/Restricted Channels (Login Required)</b></blockquote>
• Use <code>/login</code> to securely connect your Telegram account.
• Send the private link (e.g., <code>t.me/c/123...</code>).
• Bot accesses content using your authenticated session.
<blockquote><b>3️⃣ Batch Downloading Mode</b></blockquote>
• Initiate with <code>/batch</code> for multiple files.
• Follow interactive prompts for seamless processing.
<blockquote><b>🛑 Free User Limitations:</b></blockquote>
• <b>Daily Quota:</b> 5 Files / 24 Hours
• <b>File Size Cap:</b> 2GB Maximum
<blockquote><b>💎 Premium Membership Benefits:</b></blockquote>
• Unlimited Downloads & No Restrictions.
• Priority Support & Advanced Features.
"""
    ABOUT_TXT = f"""<b>ℹ️ About This Bot</b>
<blockquote><b>╭────[ 🧩 Technical Stack ]────⍟</b>
<b>├⍟ 🤖 Bot Name : <a href=http://t.me/Nawaab_SaveRestrictionBot>Save Content Bot</a></b>
<b>├⍟ 👨‍💻 Developer : <a href={OWNER_LINK}>MS BRO</a></b>
<b>├⍟ 📚 Library : <a href='https://docs.pyrogram.org/'>Pyrogram</a></b>
<b>├⍟ 🐍 Language : <a href='https://www.python.org/'>Python</a></b>
<b>├⍟ 🗄 Database : <a href='https://www.mongodb.com/'>MongoDB</a></b>
<b>├⍟ 📡 Hosting : Dedicated High-Speed VPS & Heroku</b>
<b>╰───────────────⍟</b></blockquote>
"""
    PREMIUM_TEXT = f"""<b>💎 Premium Membership Plans</b>
<b>Unlock Unlimited Access & Advanced Features!</b>
<blockquote><b>✨ Key Benefits:</b>
<b>♾️ Unlimited Daily Downloads</b>
<b>📂 Support for 4GB+ File Sizes</b>
<b>⚡ Instant Processing (Zero Delay)</b>
<b>🖼 Customizable Thumbnails</b>
<b>📝 Personalized Captions</b>
<b>🛂 24/7 Priority Support</b></blockquote>
<blockquote><b>💳 Pricing Options:</b></blockquote>
• <b>1 Week:</b> ₹50 / $0.5
• <b>1 Month:</b> ₹150 / $1.5
• <b>3 Month:</b> ₹300 / $3
<blockquote><b>👇 Secure Payment:</b></blockquote>
<b>💸 Now Only PhonePe Gift Card Accepting.</b>
<b>📸 Send Your Paid PhonePe Gift Card Number And Pin Number to Owner Id:</b> {OWNER_USERNAME}
<i>After Payment: Send Screenshot of Gift Card to Admin for Instant Activation.</i>
"""
    PROGRESS_BAR = """\
<b>⚡ Processing Task...</b>
<blockquote>
<b>Progress: {bar} {percentage:.1f}%</b>
<b>🚀 Speed:</b> <code>{speed}/s</code>
<b>💾 Size:</b> <code>{current} of {total}</code>
<b>⏱ Elapsed:</b> <code>{elapsed}</code>
<b>⏳ ETA:</b> <code>{eta}</code>
</blockquote>
"""
    CAPTION = f"""<b><a href="{CHANNEL_LINK}"></a></b>\n\n<b>⚜️ Powered By : <a href="{OWNER_LINK}">{CHANNEL_NAME} 😎</a></b>"""
    LIMIT_REACHED = """<b>🚫 Daily Limit Exceeded</b>
<b>Your 5 free saves for today have been used.</b>
<i>Quota resets automatically after 24 hours from first download.</i>
<blockquote><b>🔓 Upgrade to Premium for Unlimited Access!</b></blockquote>
Remove all restrictions and enjoy seamless downloading.
"""
    SIZE_LIMIT = """<b>⚠️ File Size Exceeded</b>
<b>Free tier limited to 2GB per file.</b>
<blockquote><b>🔓 Upgrade to Premium</b></blockquote>
Download files up to 4GB and beyond with no limits!
"""
def humanbytes(size):
    if not size:
        return "0B"
    power = 2**10
    n = 0
    Dic_powerN = {0: ' ', 1: 'K', 2: 'M', 3: 'G', 4: 'T'}
    while size > power:
        size /= power
        n += 1
    return str(round(size, 2)) + " " + Dic_powerN[n] + 'B'
def TimeFormatter(milliseconds: int) -> str:
    seconds, milliseconds = divmod(int(milliseconds), 1000)
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    days, hours = divmod(hours, 24)
    tmp = ((str(days) + "d, ") if days else "") + \
        ((str(hours) + "h, ") if hours else "") + \
        ((str(minutes) + "m, ") if minutes else "") + \
        ((str(seconds) + "s, ") if seconds else "")
    return tmp[:-2] if tmp else "0s"
class batch_temp(object):
    IS_BATCH = {}
def get_message_type(msg):
    if getattr(msg, 'document', None): return "Document"
    if getattr(msg, 'video', None): return "Video"
    if getattr(msg, 'photo', None): return "Photo"
    if getattr(msg, 'audio', None): return "Audio"
    # --- Group content (voice notes, GIFs, stickers, round videos, polls ...) ---
    if getattr(msg, 'voice', None): return "Voice"
    if getattr(msg, 'video_note', None): return "VideoNote"
    if getattr(msg, 'animation', None): return "Animation"
    if getattr(msg, 'sticker', None): return "Sticker"
    if getattr(msg, 'poll', None): return "Poll"
    if getattr(msg, 'contact', None): return "Contact"
    if getattr(msg, 'venue', None): return "Venue"
    if getattr(msg, 'location', None): return "Location"
    if getattr(msg, 'dice', None): return "Dice"
    if getattr(msg, 'text', None): return "Text"
    return None
# message type -> attribute that holds the downloadable media
FILE_MEDIA_ATTR = {
    "Document": "document", "Video": "video", "Photo": "photo", "Audio": "audio",
    "Voice": "voice", "VideoNote": "video_note", "Animation": "animation", "Sticker": "sticker",
}
# types whose Telegram-side thumbnail we can reuse
THUMB_TYPES = ("Video", "Document", "Animation", "VideoNote", "Audio")
# messages that have no file: they are re-created by the bot, nothing to download
NON_FILE_TYPES = ("Poll", "Contact", "Venue", "Location", "Dice")
async def copy_public_message(client, message, chat, msgid, dest=None):
    """Copy one post of a public channel/group. One retry on FloodWait / slow-mode.
    dest = target chat id from /setchat (None -> the user's own bot chat)."""
    kwargs = dict(chat_id=dest or message.chat.id, from_chat_id=chat, message_id=msgid)
    if not dest:
        kwargs["reply_to_message_id"] = message.id
    try:
        return await client.copy_message(**kwargs)
    except Exception as e:
        if type(e).__name__ in ("FloodWait", "SlowmodeWait"):
            await asyncio.sleep(min(int(getattr(e, "value", 1)), 60) + 1)
            return await client.copy_message(**kwargs)
        raise
_ME_CACHE = {}
async def ensure_account_me(acc, user_data):
    """A Pyrogram client that was only connect()-ed (not start()-ed) has client.me = None.
    Uploading a file then crashes with: 'NoneType' object has no attribute 'is_premium'.
    Load (and cache) the account's own profile so uploads/downloads work."""
    if getattr(acc, "me", None) is not None:
        return
    me = _ME_CACHE.get(user_data)
    if me is None:
        try:
            me = await acc.get_me()
        except Exception as e:
            if type(e).__name__ in ("AuthKeyUnregistered", "AuthKeyInvalid", "SessionRevoked",
                                    "SessionExpired", "UserDeactivated", "UserDeactivatedBan"):
                raise      # the saved login is dead -> reported as "Authentication Failed"
            logger.error(f"Could not load the account profile: {e}")
            return
        _ME_CACHE[user_data] = me
    acc.me = me
async def probe_message(client, chat, msgid):
    """What does the BOT see at this id?  Returns:
       "ok"      -> a real message (bot can read this chat)
       "service" -> a real service message (joined / pinned / topic created ...)
       "empty"   -> Telegram returned an empty message. IMPORTANT: for a group the bot has NOT
                    joined this also means "bot is not allowed to read it", so it is NOT
                    proof that the message was deleted.
       "error"   -> the bot cannot access the chat at all
    """
    try:
        m = await client.get_messages(chat, msgid)
    except Exception:
        return "error"
    if m is None or getattr(m, "empty", False):
        return "empty"
    if getattr(m, "service", None):
        return "service"
    return "ok"
async def send_non_file_message(client, chat_id, msg, msg_type):
    """Re-create poll / contact / location / venue / dice messages."""
    try:
        if msg_type == "Poll":
            poll = msg.poll
            options = [str(o.text) for o in poll.options]
            try:
                kwargs = dict(is_anonymous=poll.is_anonymous, allows_multiple_answers=bool(poll.allows_multiple_answers))
                if str(getattr(poll.type, "name", poll.type)).upper() == "QUIZ" and poll.correct_option_id is not None:
                    kwargs.update(type=poll.type, correct_option_id=poll.correct_option_id)
                await client.send_poll(chat_id, str(poll.question), options, **kwargs)
            except Exception:
                # quiz without a known answer etc. -> keep the content as plain text
                txt = f"📊 {_html.escape(str(poll.question))}\n" + "\n".join(f"• {_html.escape(o)}" for o in options)
                await client.send_message(chat_id, txt, parse_mode=enums.ParseMode.HTML)
        elif msg_type == "Contact":
            c = msg.contact
            await client.send_contact(chat_id, c.phone_number, c.first_name, last_name=c.last_name, vcard=c.vcard)
        elif msg_type == "Venue":
            v = msg.venue
            await client.send_venue(chat_id, v.location.latitude, v.location.longitude, v.title, v.address)
        elif msg_type == "Location":
            await client.send_location(chat_id, msg.location.latitude, msg.location.longitude)
        elif msg_type == "Dice":
            await client.send_dice(chat_id, emoji=msg.dice.emoji)
        return True
    except Exception as e:
        logger.error(f"Non-file message ({msg_type}) could not be sent: {e}")
        raise
# --------------------------------------------------------
# Robust Telegram link parser (public / private / batch)
# Handles links even when surrounded by extra text/spaces,
# a trailing "?single", and BOTH private link formats:
#   https://t.me/c/<channel_id>/<msg_id>
#   https://t.me/c/<channel_id>/<topic_id>/<msg_id>  (forum/topic groups)
# The old code split on "/" by fixed index, which broke (and got
# silently ignored) the moment the link had extra text around it
# or wasn't in the exact expected shape.
# --------------------------------------------------------
TME_PRIVATE_RE = re.compile(r"https?://t\.me/c/(\d+)(?:/\d+)?/(\d+)(?:-(\d+))?")
TME_BATCH_RE = re.compile(r"https?://t\.me/b/([A-Za-z0-9_]+)/(\d+)(?:-(\d+))?")
TME_PUBLIC_RE = re.compile(r"https?://t\.me/([A-Za-z0-9_]+)(?:/\d+)?/(\d+)(?:-(\d+))?")
def parse_telegram_link(text):
    """
    Finds a Telegram post link anywhere inside `text` and returns
    (kind, target, from_id, to_id):
      kind:   "private" | "batch" | "public" | None
      target: chat_id (int, already "-100"-prefixed) for private,
              or username (str) for public/batch
    Returns (None, None, None, None) if no recognizable link is found.
    """
    m = TME_PRIVATE_RE.search(text)
    if m:
        channel_id = int("-100" + m.group(1))
        from_id = int(m.group(2))
        to_id = int(m.group(3)) if m.group(3) else from_id
        return "private", channel_id, from_id, to_id
    m = TME_BATCH_RE.search(text)
    if m:
        from_id = int(m.group(2))
        to_id = int(m.group(3)) if m.group(3) else from_id
        return "batch", m.group(1), from_id, to_id
    m = TME_PUBLIC_RE.search(text)
    if m and m.group(1) not in ("c", "b"):
        from_id = int(m.group(2))
        to_id = int(m.group(3)) if m.group(3) else from_id
        return "public", m.group(1), from_id, to_id
    return None, None, None, None
async def downstatus(client, statusfile, message, chat):
    while not os.path.exists(statusfile):
        await asyncio.sleep(3)
    while os.path.exists(statusfile):
        try:
            with open(statusfile, "r", encoding='utf-8') as downread:
                txt = downread.read()
            await client.edit_message_text(chat, message.id, f"{txt}")
            await asyncio.sleep(5)
        except:
            await asyncio.sleep(5)
async def upstatus(client, statusfile, message, chat):
    while not os.path.exists(statusfile):
        await asyncio.sleep(3)
    while os.path.exists(statusfile):
        try:
            with open(statusfile, "r", encoding='utf-8') as upread:
                txt = upread.read()
            await client.edit_message_text(chat, message.id, f"{txt}")
            await asyncio.sleep(5)
        except:
            await asyncio.sleep(5)
def progress(current, total, message, type):
    if batch_temp.IS_BATCH.get(message.from_user.id):
        raise Exception("Cancelled")
    if not hasattr(progress, "cache"):
        progress.cache = {}
   
    now = time.time()
    task_id = f"{message.id}{type}"
    last_time = progress.cache.get(task_id, 0)
   
    if not hasattr(progress, "start_time"):
        progress.start_time = {}
    if task_id not in progress.start_time:
        progress.start_time[task_id] = now
       
    if (now - last_time) > 5 or current == total:
        try:
            percentage = current * 100 / total
            speed = current / (now - progress.start_time[task_id]) if (now - progress.start_time[task_id]) > 0 else 0
            eta = (total - current) / speed if speed > 0 else 0
            elapsed = now - progress.start_time[task_id]
           
            filled_length = int(percentage / 5)
            bar = '█' * filled_length + ' ' * (20 - filled_length)
           
            status = script.PROGRESS_BAR.format(
                bar=bar,
                percentage=percentage,
                current=humanbytes(current),
                total=humanbytes(total),
                speed=humanbytes(speed),
                elapsed=TimeFormatter(elapsed * 1000),
                eta=TimeFormatter(eta * 1000)
            )
           
            with open(f'{message.id}{type}status.txt', "w", encoding='utf-8') as fileup:
                fileup.write(status)
               
            progress.cache[task_id] = now
           
            if current == total:
                progress.start_time.pop(task_id, None)
                progress.cache.pop(task_id, None)
        except:
            pass
@Client.on_message(filters.command(["start"]))
async def send_start(client: Client, message: Message):
    if not await db.is_user_exist(message.from_user.id):
        await db.add_user(message.from_user.id, message.from_user.first_name)
    try:
        await message.react(emoji=random.choice(REACTIONS), big=True)
    except:
        pass
    apis = ["https://api.waifu.pics/sfw/waifu", "https://nekos.life/api/v2/img/waifu"]
    api_url = random.choice(apis)
    try:
        response = requests.get(api_url)
        response.raise_for_status()
        photo_url = response.json()["url"]
    except Exception as e:
        logger.error(f"Failed to fetch image from API: {e}")
        photo_url = "https://graph.org/file/96f7e50b37c6bd4dc5071-5eadeaf54110b8c34a.jpg"
    buttons = [
        [
            InlineKeyboardButton("💎 Buy Premium", callback_data="buy_premium"),
            InlineKeyboardButton("🆘 Help & Guide", callback_data="help_btn")
        ],
        [
            InlineKeyboardButton("⚙️ Settings Panel", callback_data="settings_btn"),
            InlineKeyboardButton("ℹ️ About Bot", callback_data="about_btn")
        ],
        [
            InlineKeyboardButton(f'📢 {CHANNEL_NAME}', url=CHANNEL_LINK),
            InlineKeyboardButton('👨‍💻 Developers', url=OWNER_LINK)
        ]
    ]
    reply_markup = InlineKeyboardMarkup(buttons)
    bot = await client.get_me()
    await client.send_photo(
        chat_id=message.chat.id,
        photo=photo_url,
        caption=script.START_TXT.format(message.from_user.mention, bot.username, bot.first_name),
        reply_markup=reply_markup,
        reply_to_message_id=message.id,
        parse_mode=enums.ParseMode.HTML
    )
@Client.on_message(filters.command(["help"]))
async def send_help(client: Client, message: Message):
    buttons = [[InlineKeyboardButton("❌ Close Menu", callback_data="close_btn")]]
    await client.send_message(
        chat_id=message.chat.id,
        text=script.HELP_TXT,
        reply_markup=InlineKeyboardMarkup(buttons),
        parse_mode=enums.ParseMode.HTML
    )
@Client.on_message(filters.command(["plan", "myplan", "premium"]))
async def send_plan(client: Client, message: Message):
    buttons = [
        [InlineKeyboardButton("📸 Send Payment Proof", url=OWNER_LINK)],
        [InlineKeyboardButton("❌ Close Menu", callback_data="close_btn")]
    ]
    await client.send_photo(
        chat_id=message.chat.id,
        photo=SUBSCRIPTION,
        caption=script.PREMIUM_TEXT,
        reply_markup=InlineKeyboardMarkup(buttons),
        parse_mode=enums.ParseMode.HTML
    )
# Handles /cancel AND the "❌ Cancel" keyboard button when no login is in progress
# (e.g. the keyboard stayed on screen after a restart). Login cancelling itself lives in session.py.
@Client.on_message(filters.command(["cancel"]) | (filters.private & filters.regex(r"(?i)^❌\s*cancel$")))
async def send_cancel(client: Client, message: Message):
    user_id = message.from_user.id
    was_running = batch_temp.IS_BATCH.get(user_id) == False
    batch_temp.IS_BATCH[user_id] = True
    await message.reply_text(
        "❌ Batch Process Cancelled Successfully." if was_running else "ℹ️ Nothing to cancel right now.",
        reply_markup=ReplyKeyboardRemove()
    )
async def settings_panel(client, callback_query):
    """
    Renders the Settings Menu with professional layout.
    """
    user_id = callback_query.from_user.id
    is_premium = await db.check_premium(user_id)
    badge = "💎 Premium Member" if is_premium else "👤 Standard User"
   
    buttons = InlineKeyboardMarkup([
        [InlineKeyboardButton("📜 Command List", callback_data="cmd_list_btn")],
        [InlineKeyboardButton("📊 Usage Stats", callback_data="user_stats_btn")],
        [InlineKeyboardButton("🗑 Dump Chat Settings", callback_data="dump_chat_btn")],
        [InlineKeyboardButton("🖼 Manage Thumbnail", callback_data="thumb_btn")],
        [InlineKeyboardButton("📝 Edit Caption", callback_data="caption_btn")],
        [InlineKeyboardButton("⬅️ Return to Home", callback_data="start_btn")]
    ])
   
    text = f"<b>⚙️ Settings Dashboard</b>\n\n<b>Account Status:</b> {badge}\n<b>User ID:</b> <code>{user_id}</code>\n\n<i>Customize and manage your bot preferences below for an optimized experience:</i>"
   
    await callback_query.edit_message_caption(
        caption=text,
        reply_markup=buttons,
        parse_mode=enums.ParseMode.HTML
    )
@Client.on_message(filters.text & filters.private & ~filters.regex("^/"))
async def save(client: Client, message: Message):
    if "https://t.me/" in message.text:
       
        is_limit_reached = await db.check_limit(message.from_user.id)
        if is_limit_reached:
            btn = InlineKeyboardMarkup([[InlineKeyboardButton("💎 Upgrade to Premium", callback_data="buy_premium")]])
            return await message.reply_photo(
                photo=SUBSCRIPTION,
                caption=script.LIMIT_REACHED,
                reply_markup=btn,
                parse_mode=enums.ParseMode.HTML
            )
       
        if batch_temp.IS_BATCH.get(message.from_user.id) == False:
            return await message.reply_text("<b>⚠️ A Task is Currently Processing.</b>\n<i>Please wait for completion or use /cancel to stop.</i>", parse_mode=enums.ParseMode.HTML)
        kind, target, fromID, toID = parse_telegram_link(message.text)
        if kind is None:
            batch_temp.IS_BATCH[message.from_user.id] = True
            return await message.reply_text(
                "<b>⚠️ Link Not Recognized</b>\n\n"
                "<i>Please send a valid Telegram post link, e.g.</i>\n"
                "<code>https://t.me/channel/123</code>\n"
                "<code>https://t.me/c/1234567890/123</code>",
                parse_mode=enums.ParseMode.HTML
            )
        uid = message.from_user.id
        # ---------- Target chat (/setchat): content goes THERE, progress/errors stay in this bot chat ----------
        dest_chat = None
        dest_title = None
        fwd_mode = None        # "bot" | "user" (only when a target chat is set)
        try:
            dump_id = await db.get_dump_chat(uid)
        except Exception:
            dump_id = None
        if dump_id:
            fwd_mode = await db.get_forward_mode(uid)
            if fwd_mode not in ("bot", "user"):
                # first time with a target chat: ask how to forward (saved globally, change with /setforwarding)
                waiting = pending_forward.get(uid)
                if waiting is not None and time.time() - waiting["ts"] > 600:
                    waiting = None      # the old question is stale (10+ min): ask again
                if waiting is not None:
                    if len(waiting["msgs"]) < 10:
                        waiting["msgs"].append(message)
                    return await message.reply_text(
                        "<b>⏳ Waiting for your choice</b>\n<i>Tap <b>As Bot</b> or <b>As User</b> on the question above. "
                        "This link will be processed right after.</i>",
                        parse_mode=enums.ParseMode.HTML
                    )
                pending_forward[uid] = {"ts": time.time(), "msgs": [message]}
                return await message.reply_text(FWD_ASK, reply_markup=fwd_buttons("fwdp"), parse_mode=enums.ParseMode.HTML)
            if fwd_mode == "bot":
                pre = await preflight(client, dump_id)
                who_txt = "the bot"
            else:
                user_session = await db.get_session(uid)
                if user_session is None:
                    return await message.reply_text(
                        "<b>🔒 Login Required For \"As User\"</b>\n"
                        "━━━━━━━━━━━━━━━━━━\n"
                        "<i>Your forwarding mode is As User, but you are not logged in.</i>\n\n"
                        "<i>Use /login, or switch with /setforwarding.</i>",
                        parse_mode=enums.ParseMode.HTML
                    )
                pre = await user_preflight(uid, user_session, dump_id)
                who_txt = "your account"
            if not pre["ok"]:
                reasons = "\n".join(f"• {_html.escape(x)}" for x in pre["problems"]) or "• The target chat is not reachable."
                return await message.reply_text(
                    f"<b>❌ Cannot Forward ({mode_label(fwd_mode)})</b>\n"
                    "━━━━━━━━━━━━━━━━━━\n"
                    f"<b>Chat ID:</b> <code>{dump_id}</code>\n\n"
                    f"{reasons}\n\n"
                    f"<i>Nothing was forwarded. Make sure {who_txt} is an admin there with 'Post Messages', "
                    "then send the link again. You can also switch with /setforwarding, use /setchat to pick another chat, "
                    "or /setchat clear to receive files here.</i>",
                    parse_mode=enums.ParseMode.HTML
                )
            dest_chat = pre["chat_id"]
            dest_title = pre["title"] or str(dest_chat)
        as_user_mode = fwd_mode == "user" and dest_chat is not None
        batch_temp.IS_BATCH[uid] = False
        is_private_link = kind == "private"
        is_public_link = kind == "public"
        total = toID - fromID + 1
        delivered = 0          # really delivered
        failed = 0             # tried but failed
        skipped = 0            # deleted / service messages
        notified = False       # an error / info message was already shown to the user
        bot_can_read = False   # the bot itself can read this public chat (so "empty" = really deleted)
        errors = []            # short reasons for the final summary (target-chat mode)
        stop_reason = None
        cur = fromID
        status = None
        last_edit = 0.0
        def status_text(head, done):
            return (
                f"<b>{head}</b>\n"
                "━━━━━━━━━━━━━━━━━━\n"
                f"<b>Target:</b> {_html.escape(str(dest_title))}\n"
                f"<b>Mode:</b> {mode_label(fwd_mode)}\n"
                f"<b>Progress:</b> <code>{done}/{total}</code>\n"
                f"<b>✅ Forwarded:</b> <code>{delivered}</code>   "
                f"<b>❌ Failed:</b> <code>{failed}</code>   "
                f"<b>⏭ Skipped:</b> <code>{skipped}</code>"
            )
        async def refresh(text, force=False):
            nonlocal last_edit
            if status is None:
                return
            now = time.time()
            if not force and now - last_edit < 3:
                return
            last_edit = now
            try:
                await status.edit_text(text, parse_mode=enums.ParseMode.HTML)
            except Exception:
                pass
        if dest_chat:
            status = await message.reply_text(status_text("📤 Forwarding Started", 0), parse_mode=enums.ParseMode.HTML)
        for msgid in range(fromID, toID + 1):
            cur = msgid
            if batch_temp.IS_BATCH.get(uid):
                break
            if dest_chat:
                await refresh(status_text("📤 Forwarding...", msgid - fromID))
            if is_public_link and not as_user_mode:
                # Public channel OR public group (users' messages + anonymous/"as group" messages)
                sent = None
                try:
                    sent = await copy_public_message(client, message, target, msgid, dest_chat)
                except Exception as e:
                    kind_ = dest_error_kind(e) if dest_chat else None
                    if kind_ == "fatal":
                        stop_reason = explain_error(e)
                        break
                    if kind_ == "content":
                        failed += 1
                        errors.append(f"#{msgid}: {explain_error(e)}")
                        continue
                if sent:
                    bot_can_read = True
                    delivered += 1
                    await db.add_traffic(uid)
                    await asyncio.sleep(1)
                    continue
                state = await probe_message(client, target, msgid)
                if state == "service":
                    skipped += 1
                    continue                     # real service message: nothing to forward
                if state == "ok":
                    bot_can_read = True          # readable but not copyable (protected) -> login flow below
                elif state == "empty" and bot_can_read:
                    skipped += 1
                    continue                     # bot reads this chat fine, so this id is really deleted
                # "empty" first-time / "error": the bot cannot read this chat (typical for groups the
                # bot has not joined) -> let the logged-in account fetch it (download & upload flow)
            user_data = await db.get_session(uid)
            if user_data is None:
                await message.reply(
                    "<b>🔒 Authentication Required</b>\n\n"
                    "<i>Access to this content requires login.</i>\n"
                    "<i>Use /login to securely authorize your account.</i>",
                    parse_mode=enums.ParseMode.HTML
                )
                notified = True
                stop_reason = "Login required to read this content. Use /login."
                break
            try:
                acc = Client(
                    "saverestricted",
                    session_string=user_data,
                    api_hash=API_HASH,
                    api_id=API_ID,
                    in_memory=True,
                    max_concurrent_transmissions=20  # Turbo: more parallel chunks for private-channel down/upload
                )
                await acc.connect()
                await ensure_account_me(acc, user_data)
            except Exception as e:
                await message.reply(f"<b>❌ Authentication Failed</b>\n\n<i>Your session may have expired. Please /logout and /login again.</i>\n<code>{e}</code>", parse_mode=enums.ParseMode.HTML)
                notified = True
                stop_reason = "Your login session is not valid. Use /logout and /login again."
                break
            result = await handle_restricted_content(
                client, acc, message, target, msgid, dest_chat, errors,
                as_user=as_user_mode, copy_first=(as_user_mode and is_public_link)
            )
            try:
                await acc.disconnect()
            except Exception:
                pass
            if result is True:
                delivered += 1
            elif result in ("notified", "failed"):
                failed += 1
                notified = notified or result == "notified"
            elif result is False:
                failed += 1
                notified = True
                stop_reason = errors[-1].split(": ", 1)[-1] if errors else "Stopped because of an error."
                break  # chat itself is not reachable / target cannot be written: stop instead of repeating the same error
            else:
                skipped += 1
            await asyncio.sleep(1)  # Turbo: shorter gap between consecutive saves
        else:
            cur = toID + 1
        was_cancelled = batch_temp.IS_BATCH.get(uid) is True and stop_reason is None
        batch_temp.IS_BATCH[uid] = True
        done = min(max(cur - fromID, 0), total)
        if status is not None:
            if stop_reason:
                head = "❌ Forwarding Stopped"
            elif was_cancelled:
                head = "🛑 Forwarding Cancelled"
            elif failed and not delivered:
                head = "❌ Forwarding Failed"
            elif failed:
                head = "⚠️ Forwarding Finished With Errors"
            elif delivered:
                head = "✅ Forwarding Complete"
            else:
                head = "ℹ️ Nothing To Forward"
            text = status_text(head, done)
            if stop_reason:
                text += f"\n\n<b>Reason:</b> <i>{_html.escape(stop_reason)}</i>"
            if errors:
                text += "\n\n<b>Errors:</b>\n" + "\n".join(f"• <code>{_html.escape(e)[:200]}</code>" for e in errors[:5])
                if len(errors) > 5:
                    text += f"\n<i>...and {len(errors) - 5} more</i>"
            if not delivered and not failed and not stop_reason and not was_cancelled:
                text += ("\n\n<i>This link has no content: the message was deleted, or it is only a service / "
                         "topic-header message. Send a message link like</i> <code>https://t.me/group/1362</code> "
                         "<i>or</i> <code>https://t.me/group/1359/1362</code>")
            await refresh(text, force=True)
        elif delivered == 0 and not notified and not was_cancelled:
            # never stay silent
            try:
                await message.reply_text(
                    "<b>ℹ️ Nothing to Save Here</b>\n\n"
                    "<i>This link has no content: the message was deleted, or it is only a service / "
                    "topic-header message (in forum groups the number right after the group name can be a topic id).</i>\n\n"
                    "<b>Send a message link instead:</b>\n"
                    "<code>https://t.me/group/1362</code>\n"
                    "<code>https://t.me/group/1359/1362</code> <i>(topic 1359, message 1362)</i>\n"
                    "<code>https://t.me/group/1362-1370</code> <i>(range)</i>",
                    parse_mode=enums.ParseMode.HTML
                )
            except Exception:
                pass
async def handle_restricted_content(client: Client, acc, message: Message, chat_target, msgid, dest=None, report=None, as_user=False, copy_first=False):
    """Download with the logged-in account and upload with the bot.
    dest   -> target chat id from /setchat (content goes there; progress stays in the user's chat)
    as_user -> the UPLOAD is made by the logged-in account (acc) instead of the bot (downloads/progress are the same)
    copy_first -> (as_user + public link) try a direct copy with the account before download & upload
    report -> list that receives short error reasons
    Returns: True delivered | False fatal (stop the range) | "notified" failed + user was told |
             "failed" failed (recorded in report) | None nothing to send (deleted / service)"""
    dest_id = dest or message.chat.id
    actor = "user" if (as_user and dest) else "bot"
    sender = acc if actor == "user" else client      # who posts into the target chat
    def _note(reason):
        if report is not None:
            report.append(f"#{msgid}: {reason}")
    async def _fail(e):
        reason = explain_error(e, actor)
        _note(reason)
        fatal = bool(dest) and dest_error_kind(e, True) == "fatal"
        if not dest:
            try:
                await client.send_message(
                    message.chat.id,
                    f"<b>❌ Could not send message #{msgid}</b>\n<code>{_html.escape(reason)[:300]}</code>",
                    parse_mode=enums.ParseMode.HTML
                )
            except Exception:
                pass
            return "notified"
        return False if fatal else "failed"
    try:
        msg: Message = await acc.get_messages(chat_target, msgid)
    except Exception as e:
        # Turbo/private-channel fix: a fresh userbot session often hasn't
        # cached this chat's peer yet, which used to fail silently
        # (PEER_ID_INVALID) and make the bot look like it "ignored" the
        # link. Force-resolve the chat once, then retry before giving up.
        try:
            await acc.get_chat(chat_target)
            msg = await acc.get_messages(chat_target, msgid)
        except Exception as e2:
            logger.error(f"Error fetching message: {e2}")
            try:
                await client.send_message(
                    message.chat.id,
                    "<b>❌ Unable to Fetch This Message</b>\n\n"
                    "<i>Make sure your logged-in account (/login) is a member "
                    "of this private channel/group and the link is correct.</i>\n"
                    f"<code>{e2}</code>",
                    reply_to_message_id=message.id,
                    parse_mode=enums.ParseMode.HTML
                )
            except Exception:
                pass
            _note("The source chat is not accessible with your logged-in account.")
            return False
    # Deleted messages and service messages (joined / pinned / title changed ...) have no content
    if msg.empty or getattr(msg, "service", None):
        return
   
    msg_type = get_message_type(msg)
    if not msg_type:
        return
    if actor == "user":
        try:
            await acc.get_chat(dest_id)     # lets the account's session know the target chat before it posts
        except Exception:
            pass
    if copy_first and actor == "user":
        # public chat + As User: a direct copy by the account is the fastest "forward"
        try:
            copied = await msg.copy(dest_id)
            if copied:
                await db.add_traffic(message.from_user.id)
                return True
        except Exception as e:
            if dest_error_kind(e, True) in ("fatal", "content"):
                return await _fail(e)
            # protected / not copyable -> normal download & upload below
    file_size = 0
    if msg_type in FILE_MEDIA_ATTR:
        file_size = int(getattr(getattr(msg, FILE_MEDIA_ATTR[msg_type], None), "file_size", 0) or 0)
   
    if file_size > FREE_LIMIT_SIZE:
        if not await db.has_unlimited_access(message.from_user.id):
            btn = InlineKeyboardMarkup([[InlineKeyboardButton("💎 Upgrade to Premium", callback_data="buy_premium")]])
            await client.send_message(
                message.chat.id,
                script.SIZE_LIMIT,
                reply_markup=btn,
                parse_mode=enums.ParseMode.HTML
            )
            return "notified"
    if msg_type == "Text":
        try:
            await sender.send_message(dest_id, msg.text, entities=msg.entities, parse_mode=enums.ParseMode.HTML)
            return True
        except Exception as e:
            return await _fail(e)
    if msg_type in NON_FILE_TYPES:
        try:
            await send_non_file_message(sender, dest_id, msg, msg_type)
            return True
        except Exception as e:
            return await _fail(e)
    await db.add_traffic(message.from_user.id)
    smsg = await client.send_message(message.chat.id, '<b>⬇️ Starting Download...</b>', reply_to_message_id=message.id, parse_mode=enums.ParseMode.HTML)
   
    temp_dir = f"downloads/{message.id}"
    if not os.path.exists(temp_dir): os.makedirs(temp_dir)
    try:
        asyncio.create_task(downstatus(client, f'{message.id}downstatus.txt', smsg, message.chat.id))
       
        file = await acc.download_media(
            msg,
            file_name=f"{temp_dir}/",
            progress=progress,
            progress_args=[message, "down"]
        )
       
        if os.path.exists(f'{message.id}downstatus.txt'): os.remove(f'{message.id}downstatus.txt')
    except Exception as e:
        if batch_temp.IS_BATCH.get(message.from_user.id) or "Cancelled" in str(e):
            if os.path.exists(temp_dir): shutil.rmtree(temp_dir)
            await smsg.edit("❌ **Task Cancelled**")
            return "notified"
        # do not fail silently: tell the user why the download did not work
        logger.error(f"Download failed for message {msgid}: {type(e).__name__}: {e}", exc_info=True)
        _note("Download failed: " + explain_error(e, "user"))
        try:
            await smsg.edit(f"<b>❌ Download Failed</b>\n<code>{_html.escape(str(e))[:300]}</code>", parse_mode=enums.ParseMode.HTML)
        except Exception:
            pass
        return "notified"
    uploaded = False
    upload_error = None
    try:
        asyncio.create_task(upstatus(client, f'{message.id}upstatus.txt', smsg, message.chat.id))
       
        ph_path = None
        thumb_id = await db.get_thumbnail(message.from_user.id)
       
        if thumb_id:
            try:
                ph_path = await client.download_media(thumb_id, file_name=f"{temp_dir}/custom_thumb.jpg")
            except Exception as e:
                logger.error(f"Failed to download custom thumb: {e}")
        if not ph_path:
            try:
                if msg_type in THUMB_TYPES:
                    _thumbs = getattr(getattr(msg, FILE_MEDIA_ATTR[msg_type], None), "thumbs", None)
                    if _thumbs:
                        ph_path = await acc.download_media(_thumbs[0].file_id, file_name=f"{temp_dir}/thumb.jpg")
            except:
                pass
        custom_caption = await db.get_caption(message.from_user.id)
        if custom_caption:
            final_caption = custom_caption.format(filename=file.split("/")[-1], size=humanbytes(file_size))
        else:
            final_caption = script.CAPTION.format(file_name=file.split("/")[-1])
            if msg.caption:
                # .html keeps the original formatting AND escapes characters like < > & (they used to break the upload)
                try:
                    _cap_html = msg.caption.html
                except Exception:
                    _cap_html = _html.escape(str(msg.caption))
                final_caption += f"\n\n{_cap_html}"
        if msg_type == "Document":
            await sender.send_document(dest_id, file, thumb=ph_path, caption=final_caption, progress=progress, progress_args=[message, "up"])
        elif msg_type == "Video":
            await sender.send_video(dest_id, file, duration=msg.video.duration, width=msg.video.width, height=msg.video.height, thumb=ph_path, caption=final_caption, progress=progress, progress_args=[message, "up"])
        elif msg_type == "Audio":
            await sender.send_audio(dest_id, file, thumb=ph_path, caption=final_caption, progress=progress, progress_args=[message, "up"])
        elif msg_type == "Photo":
            await sender.send_photo(dest_id, file, caption=final_caption)
        elif msg_type == "Voice":
            await sender.send_voice(dest_id, file, duration=msg.voice.duration or 0, caption=final_caption, progress=progress, progress_args=[message, "up"])
        elif msg_type == "VideoNote":
            await sender.send_video_note(dest_id, file, duration=msg.video_note.duration or 0, length=msg.video_note.length or 240, thumb=ph_path, progress=progress, progress_args=[message, "up"])
        elif msg_type == "Animation":
            await sender.send_animation(dest_id, file, duration=msg.animation.duration or 0, width=msg.animation.width or 0, height=msg.animation.height or 0, thumb=ph_path, caption=final_caption, progress=progress, progress_args=[message, "up"])
        elif msg_type == "Sticker":
            await sender.send_sticker(dest_id, file)
        uploaded = True
       
    except Exception as e:
         upload_error = e
         logger.error(f"Upload failed for message {msgid} (sender: {actor}): {type(e).__name__}: {e}", exc_info=True)
         try:
             await smsg.edit(f"Upload Failed: {e}")
         except Exception:
             pass
    if os.path.exists(f'{message.id}upstatus.txt'): os.remove(f'{message.id}upstatus.txt')
    if os.path.exists(temp_dir): shutil.rmtree(temp_dir)
    await client.delete_messages(message.chat.id, [smsg.id])
    if uploaded:
        return True
    reason = explain_error(upload_error, actor)
    _note(reason)
    try:
        # the status message above is deleted, so keep the reason visible
        await client.send_message(
            message.chat.id,
            f"<b>❌ Upload Failed</b> <i>(message #{msgid})</i>\n<code>{_html.escape(reason)[:300]}</code>",
            parse_mode=enums.ParseMode.HTML
        )
    except Exception:
        pass
    if dest and dest_error_kind(upload_error, True) == "fatal":
        return False
    return "notified"
@Client.on_callback_query()
async def button_callbacks(client: Client, callback_query: CallbackQuery):
    data = callback_query.data
    message = callback_query.message
    if not message: return
   # --- DEVELOPER INFO ---
    if data == "dev_info":
        await callback_query.answer(
            text=dev_text,
            show_alert=True
        )
    elif data == "channels_info":
        await callback_query.answer(
            text=channels_text,
            show_alert=True
        )
    elif data == "settings_btn":
        await settings_panel(client, callback_query)
    elif data == "buy_premium":
        buttons = [
            [InlineKeyboardButton("📸 Send Payment Proof", url=OWNER_LINK)],
            [InlineKeyboardButton("⬅️ Back to Home", callback_data="start_btn")]
        ]
        await client.edit_message_media(
            chat_id=message.chat.id,
            message_id=message.id,
            media=InputMediaPhoto(
                media=SUBSCRIPTION,
                caption=script.PREMIUM_TEXT
            ),
            reply_markup=InlineKeyboardMarkup(buttons)
        )
    elif data == "help_btn":
        buttons = [[InlineKeyboardButton("⬅️ Back to Home", callback_data="start_btn")]]
        await client.edit_message_caption(
            chat_id=message.chat.id,
            message_id=message.id,
            caption=script.HELP_TXT,
            reply_markup=InlineKeyboardMarkup(buttons),
            parse_mode=enums.ParseMode.HTML
        )
  
    elif data == "about_btn":
        buttons = [[InlineKeyboardButton("⬅️ Back to Home", callback_data="start_btn")]]
        await client.edit_message_caption(
            chat_id=message.chat.id,
            message_id=message.id,
            caption=script.ABOUT_TXT,
            reply_markup=InlineKeyboardMarkup(buttons),
            parse_mode=enums.ParseMode.HTML
        )
    elif data == "start_btn":
        bot = await client.get_me()
        apis = ["https://api.waifu.pics/sfw/waifu", "https://nekos.life/api/v2/img/waifu"]
        api_url = random.choice(apis)
        try:
            response = requests.get(api_url)
            response.raise_for_status()
            photo_url = response.json()["url"]
        except Exception as e:
            logger.error(f"Failed to fetch image from API: {e}")
            photo_url = "https://graph.org/file/e2da63735f5a0c0110538-2001962c850d6624c4.jpg"
        buttons = [
            [
                InlineKeyboardButton("💎 Buy Premium", callback_data="buy_premium"),
                InlineKeyboardButton("🆘 Help & Guide", callback_data="help_btn")
            ],
            [
                InlineKeyboardButton("⚙️ Settings Panel", callback_data="settings_btn"),
                InlineKeyboardButton("ℹ️ About Bot", callback_data="about_btn")
            ],
            [
                InlineKeyboardButton(f'📢 {CHANNEL_NAME}', url=CHANNEL_LINK),
                InlineKeyboardButton('👨‍💻 Developers', url=OWNER_LINK)
            ]
        ]
        await client.edit_message_media(
            chat_id=message.chat.id,
            message_id=message.id,
            media=InputMediaPhoto(
                media=photo_url,
                caption=script.START_TXT.format(callback_query.from_user.mention, bot.username, bot.first_name)
            ),
            reply_markup=InlineKeyboardMarkup(buttons)
        )
    elif data == "close_btn":
        await message.delete()
    elif data in ["cmd_list_btn", "user_stats_btn", "dump_chat_btn", "thumb_btn", "caption_btn"]:
        pass
    await callback_query.answer()
