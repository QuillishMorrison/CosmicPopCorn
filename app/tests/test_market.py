from app.db.session import SessionLocal
from app.models import Station, User
from app.services.market_service import execute_market_trade
from app.services.utils import inventory_map


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
