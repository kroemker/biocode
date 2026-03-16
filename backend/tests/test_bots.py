"""End-to-end tests for bot CRUD and publish endpoints."""
from httpx import AsyncClient

from tests.conftest import auth, login, register

BOT_CODE = '=> action = "wait"'


async def test_create_bot(client: AsyncClient):
    await register(client, "alice")
    token = await login(client, "alice")
    r = await client.post(
        "/api/bots/",
        json={"game_id": "rulixbots_v1", "name": "Sleeper", "code": BOT_CODE},
        headers=auth(token),
    )
    assert r.status_code == 201
    bot = r.json()
    assert bot["name"] == "Sleeper"
    assert bot["game_id"] == "rulixbots_v1"
    assert bot["version"] == 1
    assert bot["is_published"] is False


async def test_create_bot_requires_auth(client: AsyncClient):
    r = await client.post(
        "/api/bots/",
        json={"game_id": "rulixbots_v1", "name": "Ghost", "code": BOT_CODE},
    )
    assert r.status_code == 401


async def test_list_my_bots(client: AsyncClient):
    await register(client, "bob")
    token = await login(client, "bob")
    for name in ("Bot1", "Bot2"):
        await client.post(
            "/api/bots/",
            json={"game_id": "rulixbots_v1", "name": name, "code": BOT_CODE},
            headers=auth(token),
        )
    r = await client.get("/api/bots/", headers=auth(token))
    assert r.status_code == 200
    names = [b["name"] for b in r.json()]
    assert "Bot1" in names and "Bot2" in names


async def test_get_own_bot_includes_code(client: AsyncClient):
    await register(client, "carol")
    token = await login(client, "carol")
    r = await client.post(
        "/api/bots/",
        json={"game_id": "rulixbots_v1", "name": "Carol", "code": BOT_CODE},
        headers=auth(token),
    )
    bot_id = r.json()["id"]
    r = await client.get(f"/api/bots/{bot_id}", headers=auth(token))
    assert r.status_code == 200
    assert r.json()["code"] == BOT_CODE


async def test_cannot_get_other_users_bot(client: AsyncClient):
    await register(client, "dan")
    token_dan = await login(client, "dan")
    r = await client.post(
        "/api/bots/",
        json={"game_id": "rulixbots_v1", "name": "DanBot", "code": BOT_CODE},
        headers=auth(token_dan),
    )
    bot_id = r.json()["id"]

    await register(client, "eve")
    token_eve = await login(client, "eve")
    r = await client.get(f"/api/bots/{bot_id}", headers=auth(token_eve))
    assert r.status_code == 403


async def test_update_bot_increments_version(client: AsyncClient):
    await register(client, "frank")
    token = await login(client, "frank")
    r = await client.post(
        "/api/bots/",
        json={"game_id": "rulixbots_v1", "name": "Frank", "code": BOT_CODE},
        headers=auth(token),
    )
    bot_id = r.json()["id"]

    r = await client.patch(
        f"/api/bots/{bot_id}",
        json={"code": '=> action = "move_e"'},
        headers=auth(token),
    )
    assert r.status_code == 200
    assert r.json()["version"] == 2


async def test_publish_bot(client: AsyncClient):
    await register(client, "grace")
    token = await login(client, "grace")
    r = await client.post(
        "/api/bots/",
        json={"game_id": "rulixbots_v1", "name": "Grace", "code": BOT_CODE},
        headers=auth(token),
    )
    bot_id = r.json()["id"]
    r = await client.post(f"/api/bots/{bot_id}/publish", headers=auth(token))
    assert r.status_code == 200
    assert r.json()["is_published"] is True


async def test_published_bot_appears_in_game_bots_list(client: AsyncClient):
    await register(client, "hank")
    token = await login(client, "hank")
    r = await client.post(
        "/api/bots/",
        json={"game_id": "rulixbots_v1", "name": "HankBot", "code": BOT_CODE},
        headers=auth(token),
    )
    bot_id = r.json()["id"]
    await client.post(f"/api/bots/{bot_id}/publish", headers=auth(token))

    r = await client.get("/api/games/rulixbots_v1/bots")
    assert r.status_code == 200
    names = [b["name"] for b in r.json()]
    assert "HankBot" in names


async def test_unpublished_bot_not_in_game_bots_list(client: AsyncClient):
    await register(client, "iris")
    token = await login(client, "iris")
    await client.post(
        "/api/bots/",
        json={"game_id": "rulixbots_v1", "name": "Secret", "code": BOT_CODE},
        headers=auth(token),
    )
    r = await client.get("/api/games/rulixbots_v1/bots")
    assert r.status_code == 200
    names = [b["name"] for b in r.json()]
    assert "Secret" not in names
