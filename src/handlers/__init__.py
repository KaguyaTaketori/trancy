"""Handlers package — split from the monolithic handlers.py."""

from .translation import (
    do_translate_and_edit,
    translate_reply_cmd,
    tr_cmd,
    t_cmd,
    rr_cmd,
    r_cmd,
    auto_translate_handler,
)
from .settings import (
    setkey_cmd,
    auto_cmd,
    setengine_cmd,
    setmodel_cmd,
    setlang_cmd,
    sethome_cmd,
    addapi_cmd,
    editapi_cmd,
    delapi_cmd,
)
from .vocab_handlers import (
    vocab_cmd,
    vocab_review_response,
    quiz_cmd,
    write_cmd,
)
from .utility import (
    help_cmd,
    status_cmd,
    ping_cmd,
    detect_cmd,
    copy_cmd,
    len_cmd,
)

__all__ = [
    # translation
    "do_translate_and_edit",
    "translate_reply_cmd",
    "tr_cmd",
    "t_cmd",
    "rr_cmd",
    "r_cmd",
    "auto_translate_handler",
    # settings
    "setkey_cmd",
    "auto_cmd",
    "setengine_cmd",
    "setmodel_cmd",
    "setlang_cmd",
    "sethome_cmd",
    "addapi_cmd",
    "editapi_cmd",
    "delapi_cmd",
    # vocab
    "vocab_cmd",
    "vocab_review_response",
    "quiz_cmd",
    "write_cmd",
    # utility
    "help_cmd",
    "status_cmd",
    "ping_cmd",
    "detect_cmd",
    "copy_cmd",
    "len_cmd",
]
