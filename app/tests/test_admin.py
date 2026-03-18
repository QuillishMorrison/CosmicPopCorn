from sqlalchemy import select

from app.db.session import SessionLocal
from app.models import AdminRoleKey, BalanceParameter, GameContentItem, Role, User, UserRole


def grant_super_admin(username: str) -> None:
    with SessionLocal() as db:
        user = db.scalar(select(User).where(User.username == username))
        role = db.scalar(select(Role).where(Role.key == AdminRoleKey.super_admin))
        if user and role and not db.scalar(select(UserRole).where(UserRole.user_id == user.id, UserRole.role_id == role.id)):
            db.add(UserRole(user_id=user.id, role_id=role.id))
            db.commit()


def auth_headers(client, username: str = "captain_one") -> dict[str, str]:
    grant_super_admin(username)
    login = client.post("/auth/login", json={"identity": username, "password": "Captain123"})
    token = login.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_admin_requires_role(client):
    login = client.post("/auth/login", json={"identity": "captain_one", "password": "Captain123"})
    headers = {"Authorization": f"Bearer {login.json()['access_token']}"}
    denied = client.get("/admin/authz/me", headers=headers)
    assert denied.status_code == 403


def test_content_publish_and_effective_merge(client):
    headers = auth_headers(client)
    created = client.post(
        "/admin/content",
        headers=headers,
        json={
            "content_type": "module",
            "key": "solar_array",
            "display_name": "Solar Array",
            "summary": "New power module",
            "tags": ["power"],
            "payload": {
                "key": "solar_array",
                "name": "Solar Array",
                "description": "Produces passive energy.",
                "category": "power",
                "max_level": 8,
                "base_cost": {"credits": 150, "parts": 12},
                "upgrade_cost_growth": 0.4,
                "base_effect": {"energy_supply": 7},
                "effects": [{"type": "add_energy_generation", "value": 7}],
                "energy_delta": 7,
                "throughput_delta": 1,
                "crew_delta": 0,
                "crew_requirement": 0,
                "unlock_requirements": [],
                "specialization_tags": [],
                "sort_order": 15,
                "enabled": True,
                "is_visible": True,
            },
        },
    )
    assert created.status_code == 200

    published = client.post("/admin/content/module/solar_array/publish", headers=headers)
    assert published.status_code == 200

    effective = client.get("/admin/definitions/effective", headers=headers)
    assert effective.status_code == 200
    assert any(item["key"] == "solar_array" for item in effective.json()["modules"])


def test_content_rollback(client):
    headers = auth_headers(client)
    payload = {
        "content_type": "resource",
        "key": "biofoam",
        "display_name": "Biofoam",
        "summary": "First version",
        "tags": [],
        "payload": {
            "key": "biofoam",
            "name": "Biofoam",
            "description": "New industrial resource.",
            "icon_key": "biofoam",
            "rarity": "uncommon",
            "category": "industry",
            "base_price": 22,
            "sort_order": 90,
            "is_public": True,
            "is_visible": True,
            "enabled": True,
            "starting_amount": 0,
        },
    }
    client.post("/admin/content", headers=headers, json=payload)
    client.post("/admin/content/resource/biofoam/publish", headers=headers)
    payload["summary"] = "Second version"
    payload["payload"]["base_price"] = 35
    client.post("/admin/content", headers=headers, json=payload)
    client.post("/admin/content/resource/biofoam/publish", headers=headers)

    rolled = client.post("/admin/content/resource/biofoam/rollback?version=1", headers=headers)
    assert rolled.status_code == 200
    effective = client.get("/admin/definitions/effective", headers=headers).json()
    biofoam = next(item for item in effective["resources"] if item["key"] == "biofoam")
    assert biofoam["base_price"] == 22


def test_balance_publish_live(client):
    headers = auth_headers(client)
    updated = client.patch(
        "/admin/balance",
        headers=headers,
        json={"key": "market_trade_bonus_per_level", "category": "market", "scope": "global", "summary": "Buff", "value": {"value": 0.08}, "enabled": True},
    )
    assert updated.status_code == 200
    published = client.post("/admin/balance/market_trade_bonus_per_level/publish", headers=headers)
    assert published.status_code == 200

    effective = client.get("/admin/definitions/effective", headers=headers).json()
    assert effective["balance_map"]["market_trade_bonus_per_level"]["value"] == 0.08


def test_audit_log_created(client):
    headers = auth_headers(client)
    created = client.post(
        "/admin/content",
        headers=headers,
        json={
            "content_type": "resource",
            "key": "auditium",
            "display_name": "Auditium",
            "summary": "Create resource for audit trail",
            "tags": ["test"],
            "payload": {
                "key": "auditium",
                "name": "Auditium",
                "description": "Test resource for audit logging.",
                "icon_key": "auditium",
                "rarity": "common",
                "category": "test",
                "base_price": 11,
                "sort_order": 500,
                "is_public": True,
                "is_visible": True,
                "enabled": True,
                "starting_amount": 0,
            },
        },
    )
    assert created.status_code == 200
    logs = client.get("/admin/audit", headers=headers)
    assert logs.status_code == 200
    assert any(log["action_type"] == "content.save_draft" for log in logs.json())


def test_admin_can_update_player_station(client):
    headers = auth_headers(client)
    players = client.get("/admin/players", headers=headers)
    assert players.status_code == 200
    station_id = players.json()[0]["station_id"]

    updated = client.patch(
        f"/admin/players/{station_id}",
        headers=headers,
        json={
            "station_name": "Admin Tuned Relay",
            "level": 9,
            "throughput": 77.5,
            "reputation": 222,
            "inventories": [{"resource": "fuel", "amount": 333}],
            "modules": [{"module_key": "dock", "level": 5, "is_active": True}],
        },
    )
    assert updated.status_code == 200
    payload = updated.json()
    assert payload["station_name"] == "Admin Tuned Relay"
    assert payload["level"] == 9
    assert payload["throughput"] == 77.5
    assert any(item["resource"] == "fuel" and item["amount"] == 333 for item in payload["inventories"])
    assert any(item["module_key"] == "dock" and item["level"] == 5 for item in payload["modules"])


def test_admin_can_wipe_player_progress(client):
    headers = auth_headers(client)
    players = client.get("/admin/players", headers=headers)
    assert players.status_code == 200
    station_id = players.json()[0]["station_id"]

    prepared = client.patch(
        f"/admin/players/{station_id}",
        headers=headers,
        json={
            "level": 7,
            "throughput": 88,
            "inventories": [{"resource": "fuel", "amount": 999}],
            "modules": [{"module_key": "dock", "level": 6, "is_active": True}],
        },
    )
    assert prepared.status_code == 200

    wiped = client.post(f"/admin/players/{station_id}/wipe", headers=headers)
    assert wiped.status_code == 200
    payload = wiped.json()
    assert payload["level"] == 1
    assert payload["specialization"] == "freight_hub"
    assert any(item["resource"] == "fuel" and item["amount"] < 999 for item in payload["inventories"])
    assert any(item["module_key"] == "dock" and item["level"] == 1 for item in payload["modules"])
