from datetime import UTC, datetime, timedelta

from app.db.session import SessionLocal
from app.models import Station, User
from app.services.world_service import process_station_until


def auth_headers(client):
    response = client.post("/auth/login", json={"identity": "captain_one", "password": "Captain123"})
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def test_station_view_and_module_upgrade(client):
    headers = auth_headers(client)
    station = client.get("/station/me", headers=headers)
    assert station.status_code == 200
    upgrade = client.post("/station/upgrade-module", json={"module_key": "market_terminal"}, headers=headers)
    assert upgrade.status_code == 200
    module_keys = [item["module_key"] for item in upgrade.json()["modules"]]
    assert "market_terminal" in module_keys


def test_collect_rewards_endpoint(client):
    headers = auth_headers(client)
    response = client.post("/station/collect-rewards", headers=headers)
    assert response.status_code == 200
    payload = response.json()
    assert "inventories" in payload
    assert "last_processed_at" in payload


def test_station_processing_generates_report():
    with SessionLocal() as db:
        user = db.query(User).filter(User.username == "captain_one").one()
        station = db.query(Station).filter(Station.owner_id == user.id).one()
        station.last_processed_at = datetime.now(UTC) - timedelta(minutes=20)
        before_credits = next(float(item.amount) for item in station.inventories if item.resource == "credits")
        process_station_until(db, station, datetime.now(UTC))
        after_credits = next(float(item.amount) for item in station.inventories if item.resource == "credits")
        assert after_credits > before_credits
        assert len(station.reports) >= 1


def test_station_processing_does_not_create_report_every_second():
    with SessionLocal() as db:
        user = db.query(User).filter(User.username == "captain_one").one()
        station = db.query(Station).filter(Station.owner_id == user.id).one()
        before_reports = len(station.reports)
        station.last_processed_at = datetime.now(UTC) - timedelta(seconds=1)
        process_station_until(db, station, datetime.now(UTC))
        assert len(station.reports) == before_reports
