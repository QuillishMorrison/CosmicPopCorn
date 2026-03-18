def test_smoke_path(client):
    register = client.post(
        "/auth/register",
        json={
            "email": "smoke@example.com",
            "username": "smokeuser",
            "password": "Smoke1234",
            "station_name": "Smoke Relay",
            "specialization": "repair_nexus",
        },
    )
    token = register.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    assert client.get("/station/me", headers=headers).status_code == 200
    assert client.post("/market/buy", json={"resource": "parts", "quantity": 5}, headers=headers).status_code == 200
    created = client.post(
        "/contracts/create",
        json={
            "title": "Spare Parts",
            "contract_type": "delivery",
            "resource": "parts",
            "quantity": 3,
            "reward_credits": 40,
        },
        headers=headers,
    )
    assert created.status_code == 200
    assert client.get("/meta/tree", headers=headers).status_code == 200


def test_chat_smoke(client):
    login = client.post("/auth/login", json={"identity": "captain_one", "password": "Captain123"})
    headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

    global_message = client.post("/chat/global", json={"body": "Всем привет"}, headers=headers)
    assert global_message.status_code == 200

    listed = client.get("/chat/global", headers=headers)
    assert listed.status_code == 200
    assert len(listed.json()) >= 1

    threads = client.get("/chat/threads", headers=headers)
    assert threads.status_code == 200
    assert len(threads.json()) >= 1
