"""
Telegram Translation Userbot — see docstring at top for setup.
"""

import asyncio
import logging
import os
import sys
from typing import Any

from dotenv import load_dotenv
from pyrogram import Client, filters

import src.config
from src.handlers import (
    addapi_cmd,
    auto_cmd,
    auto_translate_handler,
    copy_cmd,
    delapi_cmd,
    detect_cmd,
    editapi_cmd,
    help_cmd,
    help_callback,
    len_cmd,
    ping_cmd,
    r_cmd,
    rr_cmd,
    sethome_cmd,
    setengine_cmd,
    setkey_cmd,
    setlang_cmd,
    setmodel_cmd,
    status_cmd,
    t_cmd,
    tr_cmd,
    translate_reply_cmd,
    vocab_cmd,
    vocab_review_response,
    quiz_cmd,
    write_cmd,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("translate_bot")

try:
    asyncio.get_running_loop()
except RuntimeError:
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.set_event_loop(asyncio.new_event_loop())

load_dotenv()
try:
    API_ID: int = int(os.environ["API_ID"])
    API_HASH: str = os.environ["API_HASH"]
except KeyError as missing:
    logger.critical("Missing required env variable: %s  ->  add it to .env", missing)
    sys.exit(1)

app = Client("my_account", api_id=API_ID, api_hash=API_HASH)

app.on_message(filters.me & filters.text & filters.command("help", prefixes="."))(
    help_cmd
)
app.on_message(filters.me & filters.text & filters.command("status", prefixes="."))(
    status_cmd
)
app.on_message(filters.me & filters.text & filters.command("ping", prefixes="."))(
    ping_cmd
)
app.on_message(filters.me & filters.text & filters.command("detect", prefixes="."))(
    detect_cmd
)
app.on_message(filters.me & filters.text & filters.command("copy", prefixes="."))(
    copy_cmd
)
app.on_message(filters.me & filters.text & filters.command("len", prefixes="."))(
    len_cmd
)
app.on_message(filters.me & filters.text & filters.command("setkey", prefixes="."))(
    setkey_cmd
)
app.on_message(filters.me & filters.text & filters.command("auto", prefixes="."))(
    auto_cmd
)
app.on_message(filters.me & filters.text & filters.command("setengine", prefixes="."))(
    setengine_cmd
)
app.on_message(filters.me & filters.text & filters.command("setmodel", prefixes="."))(
    setmodel_cmd
)
app.on_message(filters.me & filters.text & filters.command("setlang", prefixes="."))(
    setlang_cmd
)
app.on_message(filters.me & filters.text & filters.command("sethome", prefixes="."))(
    sethome_cmd
)
app.on_message(filters.me & filters.text & filters.command("addapi", prefixes="."))(
    addapi_cmd
)
app.on_message(filters.me & filters.text & filters.command("editapi", prefixes="."))(
    editapi_cmd
)
app.on_message(filters.me & filters.text & filters.command("delapi", prefixes="."))(
    delapi_cmd
)
app.on_message(filters.me & filters.text & filters.command("vocab", prefixes="."))(
    vocab_cmd
)
app.on_message(filters.me & filters.text & filters.command("quiz", prefixes="."))(
    quiz_cmd
)
app.on_message(filters.me & filters.text & filters.command("write", prefixes="."))(
    write_cmd
)
app.on_message(filters.me & filters.text & filters.reply & filters.regex(r"^[1-5]$"))(
    vocab_review_response
)
app.on_callback_query()(help_callback)

app.on_message(filters.me & filters.text & filters.regex(r"^\.tl$"))(
    translate_reply_cmd
)
app.on_message(filters.me & filters.text & filters.regex(r"^\.tr\s+([\s\S]+)"))(tr_cmd)
app.on_message(
    filters.me & filters.text & filters.regex(r"^\.t\s+([a-zA-Z\-,]+)\s+([\s\S]+)")
)(t_cmd)
app.on_message(filters.me & filters.text & filters.regex(r"^\.rr\s+([\s\S]+)"))(rr_cmd)
app.on_message(
    filters.me & filters.text & filters.regex(r"^\.r\s+([a-zA-Z\-,]+)\s+([\s\S]+)")
)(r_cmd)

app.on_message(filters.me & filters.text & ~filters.regex(r"^\."))(
    auto_translate_handler
)

if __name__ == "__main__":
    logger.info("🚀 Translation bot starting...")
    logger.info("🛡️  Auto-fallback gateway standing by...")
    app.run()
