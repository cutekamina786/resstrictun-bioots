# Target chat (/setchat) helpers: input parsing, verification (chat exists, bot admin, user admin,
# real test message) and human readable error explanations.
# This module has no Telegram handlers; it is imported by settings.py and start.py.
import re
import time
import html as _html

SUPPORTED_TYPES = {"CHANNEL": "Channel", "SUPERGROUP": "Group (supergroup)", "GROUP": "Group"}

# Errors that mean "the bot can no longer write into the target chat" -> stop the whole task
_FATAL_ALWAYS = {
    "ChatWriteForbidden", "ChatAdminRequired", "UserBannedInChannel", "ChannelBanned",
    "UserNotParticipant", "ChatRestricted", "ChatGuestSendForbidden",
    # the logged-in account (As User mode) is no longer usable
    "AuthKeyUnregistered", "AuthKeyInvalid", "AuthKeyDuplicated", "SessionRevoked", "SessionExpired",
    "UserDeactivated", "UserDeactivatedBan",
}
# Errors that are ambiguous when copying from a source chat (could be the source), but clearly mean
# the target when the bot is *sending* a file it already has
_FATAL_WHEN_SENDING = {"ChannelPrivate", "ChannelInvalid", "PeerIdInvalid", "ChatIdInvalid"}


def _name(e):
    return type(e).__name__


def fmt_wait(seconds):
    """1633 -> '27 min 13 s'"""
    try:
        seconds = int(seconds)
    except Exception:
        return "a while"
    h, rem = divmod(max(seconds, 0), 3600)
    m, sec = divmod(rem, 60)
    if h:
        return f"{h} h {m} min"
    if m:
        return f"{m} min {sec} s"
    return f"{sec} s"


def dest_error_kind(e, ambiguous_is_dest=False):
    """None  -> not a target problem
       'fatal'   -> bot cannot post in the target chat at all (stop the task)
       'content' -> this one content type is blocked in the target chat (skip this message)"""
    n = _name(e)
    if n in _FATAL_ALWAYS:
        return "fatal"
    if ambiguous_is_dest and n in _FATAL_WHEN_SENDING:
        return "fatal"
    if n.startswith("ChatSend") and n.endswith("Forbidden"):
        return "content"
    return None


def explain_error(e, actor="bot"):
    """Short, human readable English reason for a Telegram / generic error.
    actor = 'bot' or 'user' (As User mode talks about 'Your account')."""
    n = _name(e)
    who = "Your account" if actor == "user" else "The bot"
    fix = ("Make sure your account is an admin with the 'Post Messages' permission."
           if actor == "user" else "Make the bot an admin with the 'Post Messages' permission.")
    if n in ("ChatWriteForbidden", "ChatAdminRequired", "ChatRestricted", "ChatGuestSendForbidden"):
        return f"{who} is not allowed to post in the target chat. {fix}"
    if n in ("UserBannedInChannel", "ChannelBanned"):
        return f"{who} is banned or restricted in the target chat."
    if n == "UserNotParticipant":
        return f"{who} is not a member of the target chat any more."
    if n in ("ChannelPrivate", "ChannelInvalid", "PeerIdInvalid", "ChatIdInvalid"):
        return (f"The target chat is not accessible. {who} was removed from it, "
                "or the chat ID is wrong.")
    if n in ("AuthKeyUnregistered", "AuthKeyInvalid", "AuthKeyDuplicated", "SessionRevoked",
             "SessionExpired", "UserDeactivated", "UserDeactivatedBan"):
        return "Your login session is no longer valid. Use /logout and then /login again."
    if n.startswith("ChatSend") and n.endswith("Forbidden"):
        return "This content type is blocked in the target chat by its permissions."
    if n in ("FloodWait", "SlowmodeWait"):
        return f"Telegram rate limit ({n}): wait {fmt_wait(getattr(e, 'value', 0))} and try again."
    if n == "MediaCaptionTooLong":
        return "The caption is too long for Telegram."
    if n == "Cancelled" or "Cancelled" in str(e):
        return "Cancelled."
    text = str(e).strip().replace("\n", " ")
    return f"{n}: {text[:200]}" if text else n


# --------------------------------------------------------------------------------------
# Input parsing
# --------------------------------------------------------------------------------------
def parse_target_input(raw):
    """Returns (candidates, error). candidates is a list of references to try with get_chat."""
    raw = (raw or "").strip()
    if not raw:
        return [], "Please send a chat ID, @username or a link."
    m = re.search(r"(?:https?://)?(?:t|telegram)\.me/c/(\d+)", raw)
    if m:
        return [int("-100" + m.group(1))], None
    if re.search(r"(?:https?://)?(?:t|telegram)\.me/(?:\+|joinchat/)", raw):
        return [], ("Invite links cannot be used as a target. Send the numeric chat ID "
                    "(like -1001234567890) or the @username of the chat.")
    m = re.search(r"(?:https?://)?(?:t|telegram)\.me/([A-Za-z][A-Za-z0-9_]{3,31})", raw)
    if m:
        return [m.group(1)], None
    if raw.startswith("@"):
        raw = raw[1:]
    if re.fullmatch(r"-?\d+", raw):
        n = int(raw)
        if n < 0:
            return [n], None
        # a positive number is most likely a channel/supergroup id typed without the -100 prefix
        return [int("-100" + raw), n], None
    if re.fullmatch(r"[A-Za-z][A-Za-z0-9_]{3,31}", raw):
        return [raw], None
    return [], ("That does not look like a chat ID, @username or link.\n"
                "Example: -1001234567890 or @mychannel")


# --------------------------------------------------------------------------------------
# Verification
# --------------------------------------------------------------------------------------
def _status(member):
    s = getattr(member, "status", None)
    return str(getattr(s, "name", s)).upper()


def _lookup_error(e):
    n = _name(e)
    if n in ("UsernameNotOccupied", "UsernameInvalid"):
        return "No chat exists with that username."
    return ("The bot cannot see this chat. Either the ID/username is wrong, or the bot has not been "
            "added there. Add the bot to the chat (as admin for channels) and try again.")


async def inspect_target(client, candidates, user_id=None, owner_id=None, send_test=False):
    """Check a target chat. Never raises. Returns a dict:
    ok, chat_id, title, type_label, bot_status, bot_admin, user_status, test, problems[], warnings[]"""
    rep = {"ok": False, "chat_id": None, "title": None, "type_label": None, "bot_status": None,
           "bot_admin": False, "user_status": None, "test": None, "problems": [], "warnings": []}
    chat, last = None, None
    for ref in candidates:
        try:
            chat = await client.get_chat(ref)
            tname = str(getattr(chat.type, "name", chat.type)).upper()
            if tname in SUPPORTED_TYPES or len(candidates) == 1 or ref == candidates[-1]:
                break
            chat = None  # e.g. a positive id resolved to a user; try the next candidate
        except Exception as e:
            last = e
            chat = None
    if chat is None:
        rep["problems"].append(_lookup_error(last) if last else "Chat not found.")
        return rep

    rep["chat_id"] = chat.id
    rep["title"] = getattr(chat, "title", None) or getattr(chat, "first_name", None) or "Unknown"
    tname = str(getattr(chat.type, "name", chat.type)).upper()
    rep["type_label"] = SUPPORTED_TYPES.get(tname, tname.title())
    if tname not in SUPPORTED_TYPES:
        rep["problems"].append("Only channels and groups can be used as a target "
                               f"(this one is a {rep['type_label']}).")
        return rep
    is_channel = tname == "CHANNEL"

    # ---- is the bot in the chat, and is it admin? ----
    try:
        me = getattr(client, "me", None) or await client.get_me()
        cm = await client.get_chat_member(chat.id, me.id)
    except Exception as e:
        if "NotParticipant" in _name(e):
            rep["bot_status"] = "NOT A MEMBER"
            rep["problems"].append("The bot is not a member of this chat. Add the bot "
                                   + ("as an admin with 'Post Messages' permission." if is_channel
                                      else "(admin is recommended)."))
        else:
            rep["problems"].append("Could not read the bot's status in this chat: " + explain_error(e))
        return rep

    st = _status(cm)
    rep["bot_status"] = st
    if st == "OWNER":
        rep["bot_admin"] = True
    elif st == "ADMINISTRATOR":
        rep["bot_admin"] = True
        priv = getattr(cm, "privileges", None)
        if is_channel and priv is not None and getattr(priv, "can_post_messages", True) is False:
            rep["problems"].append("The bot is an admin but the 'Post Messages' permission is OFF. "
                                   "Turn it on in the channel's admin settings.")
    elif st == "MEMBER":
        if is_channel:
            rep["problems"].append("The bot is only a subscriber of this channel. Promote it to admin "
                                   "with the 'Post Messages' permission.")
        else:
            rep["warnings"].append("The bot is not an admin of this group. Forwarding works only if members "
                                   "are allowed to send messages/media there. Making the bot admin is recommended.")
    elif st == "RESTRICTED":
        perms = getattr(cm, "permissions", None)
        if perms is not None and getattr(perms, "can_send_messages", True) is False:
            rep["problems"].append("The bot is restricted in this chat and cannot send messages.")
        else:
            rep["warnings"].append("The bot is restricted in this chat. Some content types may be blocked. "
                                   "Making the bot admin is recommended.")
    else:  # BANNED / LEFT / unknown
        rep["problems"].append(f"The bot cannot post here (status: {st.title()}). Add it back as admin.")
    if rep["problems"]:
        return rep

    # ---- is the person who sets it an admin of that chat? (stops people using someone else's chat) ----
    if user_id is not None and not (owner_id is not None and int(user_id) == int(owner_id)):
        try:
            um = await client.get_chat_member(chat.id, int(user_id))
            ust = _status(um)
            rep["user_status"] = ust
            if ust not in ("OWNER", "ADMINISTRATOR"):
                rep["problems"].append("You must be an admin or the owner of that chat to use it as your target.")
        except Exception as e:
            if "NotParticipant" in _name(e):
                rep["user_status"] = "NOT A MEMBER"
                rep["problems"].append("You are not a member of that chat. Only admins/owners can use it as a target.")
            else:
                rep["problems"].append("Could not verify that you are an admin of that chat. "
                                       "Make sure the bot is an admin there, then try again.")
        if rep["problems"]:
            return rep

    # ---- real test: send a silent message and delete it ----
    if send_test:
        try:
            t = await client.send_message(chat.id, "✅ Connection test. This message deletes itself.",
                                          disable_notification=True)
            rep["test"] = True
            try:
                await client.delete_messages(chat.id, t.id)
            except Exception:
                pass
        except Exception as e:
            rep["test"] = False
            rep["problems"].append("Test message failed: " + explain_error(e))
    rep["ok"] = not rep["problems"]
    return rep


_PRE_CACHE = {}


async def preflight(client, chat_id, ttl=30):
    """Fast re-check before a task starts (cached for a few seconds when it was OK)."""
    hit = _PRE_CACHE.get(chat_id)
    now = time.time()
    if hit and now - hit[0] < ttl:
        return hit[1]
    rep = await inspect_target(client, [chat_id])
    if rep["ok"]:
        _PRE_CACHE[chat_id] = (now, rep)
    else:
        _PRE_CACHE.pop(chat_id, None)
    return rep


def forget_preflight(chat_id=None):
    if chat_id is None:
        _PRE_CACHE.clear()
    else:
        _PRE_CACHE.pop(chat_id, None)


def esc(x):
    return _html.escape(str(x))


def format_report(rep, saved=None):
    """HTML report. saved=True/False adds a headline for the /setchat result."""
    if saved is True:
        head = "✅ <b>Target Chat Saved</b>"
    elif saved is False:
        head = "❌ <b>Target Chat NOT Saved</b>"
    else:
        head = "🎯 <b>Target Chat Status</b>"
    lines = [head, "━━━━━━━━━━━━━━━━━━"]
    if rep.get("chat_id") is not None:
        lines.append(f"<b>Title:</b> {esc(rep['title'])}")
        lines.append(f"<b>Chat ID:</b> <code>{rep['chat_id']}</code>")
        lines.append(f"<b>Type:</b> {esc(rep['type_label'])}")
        bs = rep.get("bot_status")
        if bs:
            if rep.get("bot_admin"):
                lines.append("<b>Bot admin:</b> ✅ Yes")
            else:
                lines.append(f"<b>Bot admin:</b> ❌ No ({esc(bs.title())})")
        us = rep.get("user_status")
        if us:
            lines.append("<b>You:</b> " + ("✅ Admin / Owner" if us in ("OWNER", "ADMINISTRATOR") else f"❌ {esc(us.title())}"))
        if rep.get("test") is True:
            lines.append("<b>Test message:</b> ✅ Sent and deleted")
        elif rep.get("test") is False:
            lines.append("<b>Test message:</b> ❌ Failed")
    for w in rep.get("warnings", []):
        lines.append(f"\n⚠️ <i>{esc(w)}</i>")
    for p in rep.get("problems", []):
        lines.append(f"\n❌ <i>{esc(p)}</i>")
    if saved is True:
        lines.append("\n<i>Every link you send now is forwarded straight into this chat. "
                     "Progress and errors stay here in the bot. Use /setchat clear to turn it off.</i>")
    elif saved is False:
        lines.append("\n<i>Fix the problem above and run /setchat again.</i>")
    return "\n".join(lines)


# --------------------------------------------------------------------------------------
# Forwarding mode (As Bot / As User)
# --------------------------------------------------------------------------------------
pending_forward = {}   # user_id -> [Message, ...] links waiting for the user to choose a forwarding mode

FWD_EXPLAIN = (
    "🤖 <b>As Bot</b>: the bot sends the content into your target chat. "
    "The bot must be an admin there.\n"
    "👤 <b>As User</b>: your logged-in account (/login) sends it. You must be logged in and be an "
    "admin with permission to post in the target chat (normal or anonymous admin)."
)
FWD_ASK = (
    "<b>📤 How do you want to forward?</b>\n"
    "━━━━━━━━━━━━━━━━━━\n"
    "Your target chat is set. Choose how the content should be sent there:\n\n"
    + FWD_EXPLAIN +
    "\n\n<i>Your choice is saved for all future links. Change it any time with /setforwarding.</i>"
)


def mode_label(mode):
    return {"bot": "As Bot", "user": "As User"}.get(mode, "Not chosen yet")


def fwd_buttons(prefix):
    from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    return InlineKeyboardMarkup([[
        InlineKeyboardButton("As Bot", callback_data=f"{prefix}_bot"),
        InlineKeyboardButton("As User", callback_data=f"{prefix}_user"),
    ]])


async def inspect_user_target(acc, candidates):
    """Same idea as inspect_target, but for the logged-in USER account (As User mode).
    The account must be admin/owner of the chat (channel: with 'Post Messages'). Never raises."""
    rep = {"ok": False, "chat_id": None, "title": None, "type_label": None, "user_status": None,
           "anonymous": False, "problems": [], "warnings": []}
    chat, last = None, None
    for ref in candidates:
        try:
            chat = await acc.get_chat(ref)
            tname = str(getattr(chat.type, "name", chat.type)).upper()
            if tname in SUPPORTED_TYPES or ref == candidates[-1]:
                break
            chat = None
        except Exception as e:
            last = e
            chat = None
    if chat is None:
        if last is not None and _name(last) in ("UsernameNotOccupied", "UsernameInvalid"):
            rep["problems"].append("No chat exists with that username.")
        else:
            rep["problems"].append("Your logged-in account cannot see this chat. The ID may be wrong, or your "
                                   "account is not a member of it.")
        return rep
    rep["chat_id"] = chat.id
    rep["title"] = getattr(chat, "title", None) or "Unknown"
    tname = str(getattr(chat.type, "name", chat.type)).upper()
    rep["type_label"] = SUPPORTED_TYPES.get(tname, tname.title())
    if tname not in SUPPORTED_TYPES:
        rep["problems"].append("Only channels and groups can be used as a target.")
        return rep
    is_channel = tname == "CHANNEL"
    try:
        me = await acc.get_me()
        cm = await acc.get_chat_member(chat.id, me.id)
    except Exception as e:
        if "NotParticipant" in _name(e):
            rep["user_status"] = "NOT A MEMBER"
            rep["problems"].append("Your logged-in account is not a member of this chat.")
        else:
            rep["problems"].append("Could not read your status in this chat: " + explain_error(e, "user"))
        return rep
    st = _status(cm)
    rep["user_status"] = st
    if st == "OWNER":
        pass
    elif st == "ADMINISTRATOR":
        priv = getattr(cm, "privileges", None)
        rep["anonymous"] = bool(getattr(priv, "is_anonymous", False))
        if is_channel and priv is not None and getattr(priv, "can_post_messages", True) is False:
            rep["problems"].append("Your account is an admin but the 'Post Messages' permission is OFF.")
    else:
        rep["problems"].append(f"Your logged-in account is not an admin of this chat (status: {st.title()}). "
                               "Make it an admin with the 'Post Messages' permission.")
    rep["ok"] = not rep["problems"]
    return rep


async def check_user_target(user_data, candidates):
    """Open the saved login session, check the chat, close it. Never raises."""
    from pyrogram import Client
    from config import API_ID, API_HASH
    acc = None
    try:
        acc = Client("saverestricted", session_string=user_data, api_hash=API_HASH, api_id=API_ID, in_memory=True)
        await acc.connect()
    except Exception as e:
        return {"ok": False, "chat_id": None, "title": None, "type_label": None, "user_status": None,
                "anonymous": False, "warnings": [],
                "problems": ["Your login session is not valid. Use /logout and then /login again. "
                             f"({explain_error(e, 'user')})"]}
    try:
        return await inspect_user_target(acc, candidates)
    except Exception as e:
        return {"ok": False, "chat_id": None, "title": None, "type_label": None, "user_status": None,
                "anonymous": False, "warnings": [], "problems": [explain_error(e, "user")]}
    finally:
        try:
            await acc.disconnect()
        except Exception:
            pass


_UPRE_CACHE = {}


async def user_preflight(uid, user_data, chat_id, ttl=60):
    key = (uid, chat_id)
    hit = _UPRE_CACHE.get(key)
    now = time.time()
    if hit and now - hit[0] < ttl:
        return hit[1]
    rep = await check_user_target(user_data, [chat_id])
    if rep["ok"]:
        _UPRE_CACHE[key] = (now, rep)
    else:
        _UPRE_CACHE.pop(key, None)
    return rep


def forget_user_preflight(uid=None):
    if uid is None:
        _UPRE_CACHE.clear()
    else:
        for k in [k for k in _UPRE_CACHE if k[0] == uid]:
            _UPRE_CACHE.pop(k, None)


def format_dual_report(bot_rep, user_rep, logged_in, saved=None, mode=None):
    """/setchat report: shows BOTH ways of forwarding (As Bot / As User)."""
    base = bot_rep if bot_rep.get("chat_id") is not None else (user_rep or {})
    if saved is True:
        head = "✅ <b>Target Chat Saved</b>"
    elif saved is False:
        head = "❌ <b>Target Chat NOT Saved</b>"
    else:
        head = "🎯 <b>Target Chat Status</b>"
    lines = [head, "━━━━━━━━━━━━━━━━━━"]
    if base.get("chat_id") is not None:
        lines.append(f"<b>Title:</b> {esc(base['title'])}")
        lines.append(f"<b>Chat ID:</b> <code>{base['chat_id']}</code>")
        lines.append(f"<b>Type:</b> {esc(base['type_label'])}")
    lines.append("")
    # ---- As Bot
    if bot_rep.get("ok"):
        extra = ", test message OK" if bot_rep.get("test") else ""
        lines.append(f"🤖 <b>As Bot:</b> ✅ Ready (bot is admin{extra})")
    else:
        lines.append("🤖 <b>As Bot:</b> ❌ Not ready")
        for p in bot_rep.get("problems", []):
            lines.append(f"   • <i>{esc(p)}</i>")
    for w in bot_rep.get("warnings", []):
        lines.append(f"   ⚠️ <i>{esc(w)}</i>")
    # ---- As User
    if not logged_in:
        lines.append("👤 <b>As User:</b> ➖ Not logged in (use /login to enable this mode)")
    elif user_rep and user_rep.get("ok"):
        who = "owner" if user_rep.get("user_status") == "OWNER" else "admin"
        anon = ", anonymous admin" if user_rep.get("anonymous") else ""
        lines.append(f"👤 <b>As User:</b> ✅ Ready (you are {who}{anon})")
    else:
        lines.append("👤 <b>As User:</b> ❌ Not ready")
        for p in (user_rep or {}).get("problems", []):
            lines.append(f"   • <i>{esc(p)}</i>")
    lines.append("")
    lines.append(f"<b>Forwarding mode:</b> {mode_label(mode)}")
    if saved is True:
        if mode is None:
            lines.append("<i>Send a link and I will ask how to forward. You can also use /setforwarding.</i>")
        elif mode == "bot" and not bot_rep.get("ok"):
            lines.append("<i>⚠️ Your mode is As Bot but the bot is not ready. Fix it, or switch with /setforwarding.</i>")
        elif mode == "user" and not (user_rep and user_rep.get("ok")):
            lines.append("<i>⚠️ Your mode is As User but your account is not ready. Fix it, or switch with /setforwarding.</i>")
        lines.append("<i>Progress and errors always stay here in the bot. /setchat clear turns forwarding off.</i>")
    elif saved is False:
        lines.append("<i>Neither mode works yet. Fix the problems above and run /setchat again.</i>")
    return "\n".join(lines)
