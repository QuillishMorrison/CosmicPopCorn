from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.init_db import bootstrap_data, create_schema
from app.db.session import SessionLocal
from app.models import Sector, User
from app.schemas.auth import RegisterRequest
from app.services.auth_service import register_user


def seed_database(db: Session) -> None:
    bootstrap_data(db)
    sector = db.scalar(select(Sector))
    if not sector:
        bootstrap_data(db)
    if not db.scalar(select(User).where(User.username == "captain_one")):
        register_user(
            db,
            RegisterRequest(
                email="captain1@example.com",
                username="captain_one",
                password="Captain123",
                station_name="Relay Dawn",
                specialization="freight_hub",
            ),
        )
    if not db.scalar(select(User).where(User.username == "captain_two")):
        register_user(
            db,
            RegisterRequest(
                email="captain2@example.com",
                username="captain_two",
                password="Captain123",
                station_name="Nexus Vale",
                specialization="data_exchange",
            ),
        )


def main() -> None:
    create_schema()
    with SessionLocal() as db:
        seed_database(db)


if __name__ == "__main__":
    main()
