from fastapi import status


def test_register_and_login_flow(client):
    register = client.post(
        "/auth/register",
        json={
            "email": "pilot@example.com",
            "username": "pilot_1",
            "password": "Pilot1234",
            "station_name": "Pilot Arc",
            "specialization": "freight_hub",
        },
    )
    assert register.status_code == status.HTTP_200_OK
    token = register.json()["access_token"]

    me = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me.status_code == status.HTTP_200_OK
    assert me.json()["username"] == "pilot_1"

    bad = client.post("/auth/login", json={"identity": "pilot_1", "password": "wrongpass1"})
    assert bad.status_code == status.HTTP_401_UNAUTHORIZED


def test_bruteforce_limit(client):
    for _ in range(5):
        client.post("/auth/login", json={"identity": "captain_one", "password": "badpassword1"})
    limited = client.post("/auth/login", json={"identity": "captain_one", "password": "badpassword1"})
    assert limited.status_code == status.HTTP_429_TOO_MANY_REQUESTS
