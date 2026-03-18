from __future__ import annotations

import asyncio
import contextlib
import logging

from app.core.config import get_settings
from app.db.session import SessionLocal
from app.services.world_service import world_tick


logger = logging.getLogger(__name__)
settings = get_settings()


async def world_tick_loop() -> None:
    while True:
        try:
            with SessionLocal() as db:
                result = world_tick(db)
                logger.info("World tick completed: %s", result)
        except Exception:  # noqa: BLE001
            logger.exception("World tick failed")
        await asyncio.sleep(settings.world_tick_seconds)


async def run_scheduler(stop_event: asyncio.Event) -> None:
    task = asyncio.create_task(world_tick_loop())
    await stop_event.wait()
    task.cancel()
    with contextlib.suppress(asyncio.CancelledError):
        await task
