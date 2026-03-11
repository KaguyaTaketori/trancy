"""
Telegram Translation Userbot — see docstring at top for setup.
"""

import asyncio
import logging
import os
import sys

from dotenv import load_dotenv
from pyrogram import Client, filters

from src.handlers import (
    addapi_cmd,
    auto_cmd,
    auto_translate_handler,
    copy_cmd,
    delapi_cmd,
    detect_cmd,
    editapi_cmd,
    help_cmd,
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

# ---------------------------------------------------------------------------
# Register command handlers via table-driven loop
# ---------------------------------------------------------------------------

_DOT_COMMANDS: list[tuple[str, object]] = [
    ("help",      help_cmd),
    ("status",    status_cmd),
    ("ping",      ping_cmd),
    ("detect",    detect_cmd),
    ("copy",      copy_cmd),
    ("len",       len_cmd),
    ("setkey",    setkey_cmd),
    ("auto",      auto_cmd),
    ("setengine", setengine_cmd),
    ("setmodel",  setmodel_cmd),
    ("setlang",   setlang_cmd),
    ("sethome",   sethome_cmd),
    ("addapi",    addapi_cmd),
    ("editapi",   editapi_cmd),
    ("delapi",    delapi_cmd),
    ("vocab",     vocab_cmd),
    ("quiz",      quiz_cmd),
    ("write",     write_cmd),
]

for cmd_name, handler in _DOT_COMMANDS:
    app.on_message(filters.me & filters.text & filters.command(cmd_name, prefixes="."))(handler)

# Review response (reply with 1-5)
app.on_message(filters.me & filters.text & filters.reply & filters.regex(r"^[1-5]$"))(
    vocab_review_response
)

# Regex-based translation commands
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

# Auto-translate: catch-all for non-command messages
app.on_message(filters.me & filters.text & ~filters.regex(r"^\."))(
    auto_translate_handler
)

if __name__ == "__main__":
    logger.info("Translation bot starting...")
    logger.info("Auto-fallback gateway standing by...")
    app.run()
