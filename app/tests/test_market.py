import math
from datetime import UTC, datetime, timedelta

from app.db.init_db import bootstrap_data
from app.db.session import SessionLocal
from app.models import MarketState, Sector, Station, User
from app.services.market_service import execute_market_trade
from app.services.utils import inventory_map
from app.services.world_service import maybe_spawn_event, refresh_market


def test_market_buy_changes_inventory(client):
    login = client.post("/auth/login", json={"identity": "captain_one", "password": "Captain123"})
    headers = {"Authorization": f"Bearer {login.json()['access_token']}"}
    response = client.post("/market/buy", json={"resource": "fuel", "quantity": 5}, headers=headers)
    assert response.status_code == 200


def test_market_service_sell_flow():
    with SessionLocal() as db:
        user = db.query(User).filter(User.username == "captain_one").one()
        station = db.query(Station).filter(Station.owner_id == user.id).one()
        execute_market_trade(db, station, "fuel", 5, "sell")
        fuel = next(float(item.amount) for item in station.inventories if item.resource == "fuel")
        assert fuel < 55


def test_market_roundtrip_does_not_print_money():
    with SessionLocal() as db:
        user = db.query(User).filter(User.username == "captain_one").one()
        station = db.query(Station).filter(Station.owner_id == user.id).one()
        before = inventory_map(station)
        execute_market_trade(db, station, "fuel", 10, "buy")
        execute_market_trade(db, station, "fuel", 10, "sell")
        after = inventory_map(station)
        assert after["credits"] < before["credits"]


def test_market_state_excludes_non_market_resources(client):
    login = client.post("/auth/login", json={"identity": "captain_one", "password": "Captain123"})
    headers = {"Authorization": f"Bearer {login.json()['access_token']}"}
    response = client.get("/market/state", headers=headers)

    assert response.status_code == 200
    resources = {item["resource"] for item in response.json()}
    assert "reputation" not in resources


def test_bootstrap_removes_reputation_market_state():
    with SessionLocal() as db:
        sector = db.query(Sector).one()
        existing = db.query(MarketState).filter(MarketState.sector_id == sector.id, MarketState.resource == "reputation").one_or_none()
        if existing is None:
            db.add(
                MarketState(
                    sector_id=sector.id,
                    resource="reputation",
                    price=1.0,
                    trend=0.0,
                    history=[1.0],
                )
            )
            db.commit()

        bootstrap_data(db)

        cleaned = db.query(MarketState).filter(MarketState.sector_id == sector.id, MarketState.resource == "reputation").one_or_none()
        assert cleaned is None


def test_market_refresh_sanitizes_broken_prices(monkeypatch):
    def fake_balance(_db, key, default):
        if key in {"market_price_drift_min", "market_price_drift_max"}:
            return 0.0
        return default

    monkeypatch.setattr("app.services.world_service.get_balance_number", fake_balance)

    with SessionLocal() as db:
        sector = db.query(Sector).one()
        market = db.query(MarketState).filter(MarketState.sector_id == sector.id, MarketState.resource == "data").one()
        market.price = 6.50254663135081e194
        market.history = [6.50254663135081e194, 42.0]

        refresh_market(db)

        assert math.isfinite(market.price)
        assert 1 <= market.price <= 60
        assert market.history
        assert all(math.isfinite(value) and value <= 60 for value in market.history)


def test_market_events_do_not_compound_prices_forever(monkeypatch):
    def fake_balance(_db, key, default):
        if key in {"market_price_drift_min", "market_price_drift_max"}:
            return 0.0
        return default

    monkeypatch.setattr("app.services.world_service.get_balance_number", fake_balance)

    with SessionLocal() as db:
        sector = db.query(Sector).one()
        market = db.query(MarketState).filter(MarketState.sector_id == sector.id, MarketState.resource == "data").one()
        market.price = 10.0
        market.history = [10.0]
        from app.models import WorldEvent

        db.add(
            WorldEvent(
                sector_id=sector.id,
                key="scientific_grant",
                title="Научный грант",
                description="Тестовый буст рынка данных.",
                market_effects={"data": 1.12},
                starts_at=datetime.now(UTC),
                ends_at=datetime.now(UTC) + timedelta(minutes=60),
            )
        )
        db.flush()

        for _ in range(600):
            refresh_market(db)

        assert market.price < 25
        assert all(value < 25 for value in market.history)


def test_world_events_respect_active_cooldown(monkeypatch):
    template = {
        "key": "fuel_surge",
        "title": "Всплеск спроса на топливо",
        "long_description": "Тестовое событие.",
        "duration_minutes": 60,
        "weight": 1.0,
        "conditions": {"all": [{"field": "sector_player_count", "op": ">=", "value": 1}]},
        "market_effects": {"fuel": 1.18},
        "enabled": True,
        "cooldown_minutes": 30,
    }

    def fake_balance(_db, key, default):
        if key == "world_event_spawn_chance":
            return 1.0
        return default

    monkeypatch.setattr("app.services.world_service.get_balance_number", fake_balance)
    monkeypatch.setattr("app.services.world_service.event_definitions", lambda _db: [template])

    with SessionLocal() as db:
        first = maybe_spawn_event(db)
        db.flush()
        second = maybe_spawn_event(db)

        assert first is not None
        assert second is None
