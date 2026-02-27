import asyncio
import logging
from typing import Any

logger = logging.getLogger("translate_bot")


def create_tracked_task(coro: Any) -> asyncio.Task:
    task = asyncio.create_task(coro)
    task.add_done_callback(_log_task_exception)
    return task


def _log_task_exception(task: asyncio.Task) -> None:
    if not task.cancelled() and task.exception():
        logger.error("Background task raised: %s", task.exception())


async def delete_later(message: Any, delay: int = 3) -> None:
    await asyncio.sleep(delay)
    try:
        await message.delete()
    except Exception as e:
        logger.debug("delete_later: %s", e)
