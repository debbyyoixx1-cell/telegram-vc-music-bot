import asyncio
import logging
import os

from aiohttp import web
from pyrogram import Client, filters
from pyrogram.enums import ChatType
from pyrogram.types import Message
from pytgcalls import PyTgCalls
from pytgcalls.exceptions import NoActiveGroupCall
from pytgcalls.types import MediaStream
from pytgcalls.types import StreamEnded

import queues
from config import (
    ALLOWED_CHAT_ID,
    API_HASH,
    API_ID,
    BOT_TOKEN,
    COMMAND_PREFIXES,
    LOG_CHAT_ID,
    OWNER_ID,
    SESSION_STRING,
)
from downloader import format_duration, resolve

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
log = logging.getLogger("musicbot")

# Bind one event loop before the clients are constructed.
loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)

bot = Client(
    "musicbot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN,
    in_memory=True,
)

assistant = Client(
    "assistant",
    api_id=API_ID,
    api_hash=API_HASH,
    session_string=SESSION_STRING,
    in_memory=True,
)

calls = PyTgCalls(assistant)

cmd = filters.command(
    [
        "start",
        "help",
        "play",
        "skip",
        "pause",
        "resume",
        "stop",
        "end",
        "queue",
        "now",
        "ping",
        "id",
    ],
    prefixes=COMMAND_PREFIXES,
)


def allowed(message: Message) -> bool:
    if message.chat.type == ChatType.PRIVATE:
        return True
    if ALLOWED_CHAT_ID and message.chat.id != ALLOWED_CHAT_ID:
        return False
    return True


async def ensure_assistant_in_chat(chat_id: int, message: Message) -> bool:
    """Make sure the assistant user account is a member of the group."""
    try:
        await assistant.get_chat(chat_id)
        return True
    except Exception:
        pass
    try:
        link = await bot.export_chat_invite_link(chat_id)
        await assistant.join_chat(link)
        return True
    except Exception as exc:  # noqa: BLE001
        await message.reply_text(
            "❌ Assistant account က group ထဲမဝင်နိုင်ဘူး။\n"
            "Assistant account ကို group ထဲ manual invite ပေးပါ၊ "
            "ဒါမှမဟုတ် bot ကို admin (invite users) ခွင့်ပေးပါ။\n"
            f"<code>{exc}</code>"
        )
        return False


async def start_stream(chat_id: int, track: dict) -> None:
    queues.set_now(chat_id, track)
    await calls.play(chat_id, MediaStream(track["path"], video_flags=MediaStream.Flags.IGNORE))


async def play_next(chat_id: int) -> bool:
    nxt = queues.pop(chat_id)
    if not nxt:
        queues.set_now(chat_id, None)
        try:
            await calls.leave_call(chat_id)
        except Exception:  # noqa: BLE001
            pass
        return False
    await start_stream(chat_id, nxt)
    return True


@bot.on_message(cmd & filters.regex(r"^[/!.](start|help)"))
async def help_cmd(_, message: Message):
    if not allowed(message):
        return
    await message.reply_text(
        "🎧 <b>Voice Chat Music Bot</b>\n\n"
        "<b>/play</b> &lt;song name or YouTube link&gt; — voice chat ထဲမှာ ဖွင့်မယ်\n"
        "<b>/pause</b> — ခဏရပ်\n"
        "<b>/resume</b> — ပြန်ဖွင့်\n"
        "<b>/skip</b> — နောက်သီချင်း\n"
        "<b>/queue</b> — စာရင်းကြည့်\n"
        "<b>/now</b> — အခုဖွင့်နေတဲ့သီချင်း\n"
        "<b>/stop</b> — ရပ်ပြီး voice chat ကထွက်\n"
        "<b>/ping</b> — အလုပ်လုပ်မလုပ်စစ်\n\n"
        "Group ထဲမှာ voice chat အရင်ဖွင့်ထားပါ 👍"
    )


@bot.on_message(cmd & filters.regex(r"^[/!.]ping"))
async def ping_cmd(_, message: Message):
    await message.reply_text("🏓 Pong! Bot 24/7 online.")


@bot.on_message(cmd & filters.regex(r"^[/!.]id"))
async def id_cmd(_, message: Message):
    await message.reply_text(
        f"Chat ID: <code>{message.chat.id}</code>\n"
        f"Your ID: <code>{message.from_user.id if message.from_user else '-'}</code>"
    )


@bot.on_message(cmd & filters.regex(r"^[/!.]play") & filters.group)
async def play_cmd(_, message: Message):
    if not allowed(message):
        return
    chat_id = message.chat.id
    query = " ".join(message.command[1:]).strip()
    if not query:
        await message.reply_text("သီချင်းနာမည် ဒါမှမဟုတ် YouTube link ပေးပါ။\n<code>/play shape of you</code>")
        return

    status = await message.reply_text("🔎 ရှာနေတယ်...")
    try:
        result = await resolve(query)
    except Exception as exc:  # noqa: BLE001
        log.exception("download failed")
        await status.edit_text(f"❌ ဒေါင်းလုဒ်မရဘူး။\n<code>{exc}</code>")
        return

    if not result:
        await status.edit_text("❌ ဘာမှမတွေ့ဘူး။")
        return

    info, path = result
    track = {
        "title": info["title"],
        "duration": info["duration"],
        "url": info["url"],
        "path": path,
        "requested_by": message.from_user.mention if message.from_user else "Unknown",
    }

    if not await ensure_assistant_in_chat(chat_id, message):
        await status.delete()
        return

    if queues.is_active(chat_id):
        pos = queues.push(chat_id, track)
        await status.edit_text(
            f"➕ <b>Queue #{pos}</b>\n🎵 {track['title']}\n⏱ {format_duration(track['duration'])}\n👤 {track['requested_by']}"
        )
        return

    try:
        await start_stream(chat_id, track)
    except NoActiveGroupCall:
        queues.set_now(chat_id, None)
        await status.edit_text("❌ Group မှာ voice chat မဖွင့်ရသေးဘူး။ အရင်ဖွင့်ပေးပါ။")
        return
    except Exception as exc:  # noqa: BLE001
        queues.set_now(chat_id, None)
        log.exception("stream failed")
        await status.edit_text(f"❌ Voice chat ထဲ join မရဘူး။\n<code>{exc}</code>")
        return

    await status.edit_text(
        f"▶️ <b>ဖွင့်နေပါပြီ</b>\n🎵 {track['title']}\n⏱ {format_duration(track['duration'])}\n👤 {track['requested_by']}"
    )


@bot.on_message(cmd & filters.regex(r"^[/!.]pause") & filters.group)
async def pause_cmd(_, message: Message):
    try:
        await calls.pause(message.chat.id)
        await message.reply_text("⏸ ခဏရပ်ထားတယ်။ <code>/resume</code> နဲ့ပြန်ဖွင့်ပါ။")
    except Exception:  # noqa: BLE001
        await message.reply_text("❌ ဖွင့်နေတာမရှိဘူး။")


@bot.on_message(cmd & filters.regex(r"^[/!.]resume") & filters.group)
async def resume_cmd(_, message: Message):
    try:
        await calls.resume(message.chat.id)
        await message.reply_text("▶️ ပြန်ဖွင့်လိုက်ပြီ။")
    except Exception:  # noqa: BLE001
        await message.reply_text("❌ ဖွင့်နေတာမရှိဘူး။")


@bot.on_message(cmd & filters.regex(r"^[/!.]skip") & filters.group)
async def skip_cmd(_, message: Message):
    chat_id = message.chat.id
    if not queues.is_active(chat_id):
        await message.reply_text("❌ ဖွင့်နေတာမရှိဘူး။")
        return
    if await play_next(chat_id):
        track = queues.now(chat_id)
        await message.reply_text(f"⏭ နောက်သီချင်း\n🎵 {track['title']}")
    else:
        await message.reply_text("⏹ Queue ကုန်သွားပြီ။ Voice chat ကထွက်လိုက်ပြီ။")


@bot.on_message(cmd & filters.regex(r"^[/!.](stop|end)") & filters.group)
async def stop_cmd(_, message: Message):
    chat_id = message.chat.id
    queues.clear(chat_id)
    try:
        await calls.leave_call(chat_id)
    except Exception:  # noqa: BLE001
        pass
    await message.reply_text("⏹ ရပ်ပြီး voice chat ကထွက်လိုက်ပြီ။")


@bot.on_message(cmd & filters.regex(r"^[/!.]now") & filters.group)
async def now_cmd(_, message: Message):
    track = queues.now(message.chat.id)
    if not track:
        await message.reply_text("❌ ဖွင့်နေတာမရှိဘူး။")
        return
    await message.reply_text(
        f"🎧 <b>အခုဖွင့်နေတာ</b>\n🎵 {track['title']}\n⏱ {format_duration(track['duration'])}\n👤 {track['requested_by']}"
    )


@bot.on_message(cmd & filters.regex(r"^[/!.]queue") & filters.group)
async def queue_cmd(_, message: Message):
    chat_id = message.chat.id
    current = queues.now(chat_id)
    items = queues.peek_all(chat_id)
    if not current and not items:
        await message.reply_text("📭 Queue ဗလာပဲ။")
        return
    lines = []
    if current:
        lines.append(f"▶️ {current['title']}")
    for i, t in enumerate(items, start=1):
        lines.append(f"{i}. {t['title']} — {format_duration(t['duration'])}")
    await message.reply_text("<b>📃 Queue</b>\n" + "\n".join(lines))


@calls.on_update()
async def stream_end_handler(_, update):
    if isinstance(update, StreamEnded):
        chat_id = update.chat_id
        old = queues.now(chat_id)
        if await play_next(chat_id):
            track = queues.now(chat_id)
            try:
                await bot.send_message(chat_id, f"▶️ ဆက်ဖွင့်နေပါပြီ\n🎵 {track['title']}")
            except Exception:  # noqa: BLE001
                pass
        if old:
            try:
                os.remove(old["path"])
            except OSError:
                pass


async def health_server() -> None:
    """Keeps free hosts (Koyeb/Render/Replit) happy by binding a port."""
    app = web.Application()
    app.router.add_get("/", lambda _r: web.json_response({"status": "ok", "bot": "running"}))
    app.router.add_get("/health", lambda _r: web.Response(text="ok"))
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.getenv("PORT", "8080"))
    await web.TCPSite(runner, "0.0.0.0", port).start()
    log.info("health server on :%s", port)


async def main() -> None:
    missing = [
        name
        for name, val in [
            ("API_ID", API_ID),
            ("API_HASH", API_HASH),
            ("BOT_TOKEN", BOT_TOKEN),
            ("SESSION_STRING", SESSION_STRING),
        ]
        if not val
    ]
    if missing:
        raise SystemExit(f"Missing env vars: {', '.join(missing)}")

    await health_server()
    await bot.start()
    await calls.start()
    me = await bot.get_me()
    log.info("bot started as @%s", me.username)
    if LOG_CHAT_ID or OWNER_ID:
        try:
            await bot.send_message(LOG_CHAT_ID or OWNER_ID, "✅ Music bot started.")
        except Exception:  # noqa: BLE001
            pass
    await asyncio.Event().wait()


if __name__ == "__main__":
    loop.run_until_complete(main())
