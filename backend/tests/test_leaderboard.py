"""End-to-end tests for Elo ratings and leaderboard."""
from httpx import AsyncClient

from tests.conftest import auth, create_and_publish_bot, login, register, wait_for_match

RUSHER_CODE = """\
=> action = "move_e"
abs(enemy_x - my_x) <= 1, abs(enemy_y - my_y) <= 1 => action = "attack"
"""


async def test_leaderboard_empty_initially(client: AsyncClient):
    r = await client.get("/api/leaderboard/rulixbots_v1")
    assert r.status_code == 200
    assert r.json() == []


async def test_ranked_match_creates_leaderboard_entries(client: AsyncClient):
    """After a ranked match, both players appear on the leaderboard."""
    await register(client, "alice")
    token_a = await login(client, "alice")
    bot_a = await create_and_publish_bot(client, token_a, name="Alice", code=RUSHER_CODE)

    await register(client, "bob")
    token_b = await login(client, "bob")
    bot_b = await create_and_publish_bot(client, token_b, name="Bob")

    r = await client.post(
        "/api/matches/",
        json={
            "game_id": "rulixbots_v1",
            "bot_id": bot_a["id"],
            "opponent_bot_id": bot_b["id"],
        },
        headers=auth(token_a),
    )
    match_id = r.json()["id"]
    await wait_for_match(client, match_id, token_a)

    r = await client.get("/api/leaderboard/rulixbots_v1")
    assert r.status_code == 200
    entries = r.json()
    usernames = [e["username"] for e in entries]
    assert "alice" in usernames
    assert "bob" in usernames


async def test_winner_elo_increases(client: AsyncClient):
    """The match winner's Elo must be above the starting 1000."""
    await register(client, "carol")
    token_c = await login(client, "carol")
    bot_c = await create_and_publish_bot(client, token_c, name="Carol", code=RUSHER_CODE)

    await register(client, "dan")
    token_d = await login(client, "dan")
    bot_d = await create_and_publish_bot(client, token_d, name="Dan")

    r = await client.post(
        "/api/matches/",
        json={
            "game_id": "rulixbots_v1",
            "bot_id": bot_c["id"],
            "opponent_bot_id": bot_d["id"],
        },
        headers=auth(token_c),
    )
    match_id = r.json()["id"]
    match = await wait_for_match(client, match_id, token_c)

    if match["winner_index"] is None:
        return  # draw — skip assertion

    r = await client.get("/api/leaderboard/rulixbots_v1")
    entries = {e["username"]: e for e in r.json()}
    winner_name = "carol" if match["winner_index"] == 0 else "dan"
    loser_name = "dan" if winner_name == "carol" else "carol"

    assert entries[winner_name]["elo"] > 1000
    assert entries[loser_name]["elo"] < 1000


async def test_test_match_does_not_affect_leaderboard(client: AsyncClient):
    """Unranked test matches must NOT create rating entries."""
    await register(client, "eve")
    token = await login(client, "eve")
    r = await client.post(
        "/api/bots/",
        json={"game_id": "rulixbots_v1", "name": "Eve", "code": '=> action = "wait"'},
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

    r = await client.get("/api/leaderboard/rulixbots_v1")
    usernames = [e["username"] for e in r.json()]
    assert "eve" not in usernames


async def test_leaderboard_sorted_by_elo_descending(client: AsyncClient):
    """Higher-Elo players must appear first."""
    await register(client, "frank")
    token_f = await login(client, "frank")
    bot_f = await create_and_publish_bot(client, token_f, name="Frank", code=RUSHER_CODE)

    await register(client, "grace")
    token_g = await login(client, "grace")
    bot_g = await create_and_publish_bot(client, token_g, name="Grace")

    r = await client.post(
        "/api/matches/",
        json={
            "game_id": "rulixbots_v1",
            "bot_id": bot_f["id"],
            "opponent_bot_id": bot_g["id"],
        },
        headers=auth(token_f),
    )
    match_id = r.json()["id"]
    await wait_for_match(client, match_id, token_f)

    r = await client.get("/api/leaderboard/rulixbots_v1")
    elos = [e["elo"] for e in r.json()]
    assert elos == sorted(elos, reverse=True)
