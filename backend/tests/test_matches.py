"""End-to-end tests for match creation, execution and replay retrieval."""
from httpx import AsyncClient

from tests.conftest import auth, create_and_publish_bot, login, register, wait_for_match

# A bot that simply moves east every turn
RUSHER_CODE = """\
=> action = "move_e"
abs(enemy_x - my_x) <= 1, abs(enemy_y - my_y) <= 1 => action = "attack"
"""


async def test_test_match_runs_and_completes(client: AsyncClient):
    """POST /matches/test runs a game against a sample bot and stores a replay."""
    await register(client, "alice")
    token = await login(client, "alice")

    r = await client.post(
        "/api/bots/",
        json={"game_id": "rulixbots_v1", "name": "Alice", "code": RUSHER_CODE},
        headers=auth(token),
    )
    bot_id = r.json()["id"]

    r = await client.post(
        "/api/matches/test",
        json={"game_id": "rulixbots_v1", "bot_id": bot_id, "sample_bot_name": "Rusher"},
        headers=auth(token),
    )
    assert r.status_code == 201
    match_id = r.json()["id"]

    match = await wait_for_match(client, match_id, token)
    assert match["status"] == "completed"
    assert isinstance(match["winner_index"], (int, type(None)))


async def test_test_match_replay_has_snapshots(client: AsyncClient):
    """Completed match replay must contain at least 2 turn snapshots."""
    await register(client, "bob")
    token = await login(client, "bob")

    r = await client.post(
        "/api/bots/",
        json={"game_id": "rulixbots_v1", "name": "Bob", "code": RUSHER_CODE},
        headers=auth(token),
    )
    bot_id = r.json()["id"]

    r = await client.post(
        "/api/matches/test",
        json={"game_id": "rulixbots_v1", "bot_id": bot_id, "sample_bot_name": "Wanderer"},
        headers=auth(token),
    )
    match_id = r.json()["id"]
    match = await wait_for_match(client, match_id, token)

    r = await client.get(f"/api/matches/{match_id}", headers=auth(token))
    assert r.status_code == 200
    replay = r.json()["replay"]
    assert replay is not None
    assert len(replay) >= 2  # initial state + at least one turn


async def test_test_match_unknown_sample_bot_rejected(client: AsyncClient):
    await register(client, "carol")
    token = await login(client, "carol")
    r = await client.post(
        "/api/bots/",
        json={"game_id": "rulixbots_v1", "name": "Carol", "code": '=> action = "wait"'},
        headers=auth(token),
    )
    bot_id = r.json()["id"]

    r = await client.post(
        "/api/matches/test",
        json={"game_id": "rulixbots_v1", "bot_id": bot_id, "sample_bot_name": "DoesNotExist"},
        headers=auth(token),
    )
    assert r.status_code == 404


async def test_ranked_match_between_two_players(client: AsyncClient):
    """Two players with published bots can run a ranked match."""
    await register(client, "dan")
    token_dan = await login(client, "dan")
    bot_dan = await create_and_publish_bot(client, token_dan, name="DanBot", code=RUSHER_CODE)

    await register(client, "eve")
    token_eve = await login(client, "eve")
    bot_eve = await create_and_publish_bot(client, token_eve, name="EveBot")

    r = await client.post(
        "/api/matches/",
        json={
            "game_id": "rulixbots_v1",
            "bot_id": bot_dan["id"],
            "opponent_bot_id": bot_eve["id"],
        },
        headers=auth(token_dan),
    )
    assert r.status_code == 201
    match_id = r.json()["id"]

    match = await wait_for_match(client, match_id, token_dan)
    assert match["status"] == "completed"


async def test_ranked_match_requires_published_opponent(client: AsyncClient):
    await register(client, "frank")
    token_frank = await login(client, "frank")
    bot_frank = await create_and_publish_bot(client, token_frank, name="Frank")

    await register(client, "grace")
    token_grace = await login(client, "grace")
    r = await client.post(
        "/api/bots/",
        json={"game_id": "rulixbots_v1", "name": "GraceUnpub", "code": '=> action = "wait"'},
        headers=auth(token_grace),
    )
    unpublished_bot_id = r.json()["id"]

    r = await client.post(
        "/api/matches/",
        json={
            "game_id": "rulixbots_v1",
            "bot_id": bot_frank["id"],
            "opponent_bot_id": unpublished_bot_id,
        },
        headers=auth(token_frank),
    )
    assert r.status_code == 404


async def test_my_matches_lists_own_matches(client: AsyncClient):
    await register(client, "hank")
    token = await login(client, "hank")
    r = await client.post(
        "/api/bots/",
        json={"game_id": "rulixbots_v1", "name": "Hank", "code": '=> action = "wait"'},
        headers=auth(token),
    )
    bot_id = r.json()["id"]

    r = await client.post(
        "/api/matches/test",
        json={"game_id": "rulixbots_v1", "bot_id": bot_id, "sample_bot_name": "Rusher"},
        headers=auth(token),
    )
    match_id = r.json()["id"]
    await wait_for_match(client, match_id, token)

    r = await client.get("/api/matches/my", headers=auth(token))
    assert r.status_code == 200
    ids = [m["id"] for m in r.json()]
    assert match_id in ids


async def test_get_match_without_auth(client: AsyncClient):
    """Match detail is publicly readable."""
    await register(client, "iris")
    token = await login(client, "iris")
    r = await client.post(
        "/api/bots/",
        json={"game_id": "rulixbots_v1", "name": "Iris", "code": '=> action = "wait"'},
        headers=auth(token),
    )
    bot_id = r.json()["id"]
    r = await client.post(
        "/api/matches/test",
        json={"game_id": "rulixbots_v1", "bot_id": bot_id, "sample_bot_name": "Cornerstone"},
        headers=auth(token),
    )
    match_id = r.json()["id"]
    await wait_for_match(client, match_id, token)

    r = await client.get(f"/api/matches/{match_id}")  # no auth
    assert r.status_code == 200
    assert r.json()["id"] == match_id
