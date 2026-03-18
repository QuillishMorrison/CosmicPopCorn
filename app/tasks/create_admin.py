from __future__ import annotations

import argparse

from sqlalchemy import select

from app.db.init_db import bootstrap_data, create_schema
from app.db.session import SessionLocal
from app.models import AdminRoleKey, Role, User, UserRole
from app.schemas.auth import RegisterRequest
from app.services.auth_service import register_user


def main() -> None:
    parser = argparse.ArgumentParser(description="Create or promote a super admin user.")
    parser.add_argument("--email", required=True)
    parser.add_argument("--username", required=True)
    parser.add_argument("--password", required=True)
    args = parser.parse_args()

    create_schema()
    with SessionLocal() as db:
        bootstrap_data(db)
        user = db.scalar(select(User).where(User.username == args.username.lower()))
        if not user:
            user = register_user(
                db,
                RegisterRequest(
                    email=args.email,
                    username=args.username,
                    password=args.password,
                    station_name="Admin Relay",
                    specialization="freight_hub",
                ),
            )
        role = db.scalar(select(Role).where(Role.key == AdminRoleKey.super_admin))
        if role and not db.scalar(select(UserRole).where(UserRole.user_id == user.id, UserRole.role_id == role.id)):
            db.add(UserRole(user_id=user.id, role_id=role.id))
        db.commit()
        print(f"super_admin ready: {user.username}")


if __name__ == "__main__":
    main()
