from __future__ import annotations

import os
from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient

os.environ.setdefault("DATABASE_URL", "sqlite:///./test_sector_relay.db")
os.environ.setdefault("DEV_SEED_ENABLED", "false")
os.environ.setdefault("SECRET_KEY", "test-secret-key-32-bytes-minimum!!")

from app.db.base import Base
from app.db.session import SessionLocal, engine
from app.main import app
from app.tasks.seed import seed_database


@pytest.fixture(autouse=True)
def reset_db() -> Generator[None, None, None]:
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
      seed_database(db)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def client() -> Generator[TestClient, None, None]:
    with TestClient(app) as test_client:
        yield test_client
