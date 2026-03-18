from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api import admin, auth, chat, contracts, dev, market, meta, notifications, sector, station, transfers
from app.core.config import get_settings
from app.db.init_db import bootstrap_data, create_schema
from app.db.session import SessionLocal
from app.tasks.scheduler import run_scheduler
from app.tasks.seed import seed_database


settings = get_settings()
settings.media_root_path.mkdir(parents=True, exist_ok=True)
settings.chat_upload_path.mkdir(parents=True, exist_ok=True)


@asynccontextmanager
async def lifespan(_: FastAPI):
    create_schema()
    with SessionLocal() as db:
        bootstrap_data(db)
        if settings.dev_seed_enabled:
            seed_database(db)
    stop_event = asyncio.Event()
    scheduler_task = asyncio.create_task(run_scheduler(stop_event))
    yield
    stop_event.set()
    await scheduler_task


app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    description="Sector Relay MVP backend",
    lifespan=lifespan,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.mount("/media", StaticFiles(directory=settings.media_root_path), name="media")

app.include_router(auth.router)
app.include_router(station.router)
app.include_router(market.router)
app.include_router(contracts.router)
app.include_router(meta.router)
app.include_router(sector.router)
app.include_router(transfers.router)
app.include_router(notifications.router)
app.include_router(chat.router)
app.include_router(admin.router)
app.include_router(dev.router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


def main() -> None:
    uvicorn.run("app.main:app", host=settings.api_host, port=settings.api_port, reload=settings.is_dev)


if __name__ == "__main__":
    main()
