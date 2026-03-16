"""End-to-end tests for the tournament system."""
from httpx import AsyncClient

from tests.conftest import auth, create_and_publish_bot, login, register, wait_for_tournament

RUSHER_CODE = """\
=> action = "move_e"
abs(enemy_x - my_x) <= 1, abs(enemy_y - my_y) <= 1 => action = "attack"
"""


# ------------------------------------------------------------------ #
# CRUD / validation                                                   #
# ------------------------------------------------------------------ #

async def test_create_tournament(client: AsyncClient):
    await register(client, "alice")
    token = await login(client, "alice")

    r = await client.post(
        "/api/tournaments/",
        json={"name": "Test Cup", "game_id": "rulixbots_v1", "max_participants": 4},
        headers=auth(token),
    )
    assert r.status_code == 201
    t = r.json()
    assert t["name"] == "Test Cup"
    assert t["status"] == "registration"
    assert t["max_participants"] == 4
    assert t["participant_count"] == 0


async def test_create_tournament_requires_auth(client: AsyncClient):
    r = await client.post(
        "/api/tournaments/",
        json={"name": "Ghost Cup", "game_id": "rulixbots_v1", "max_participants": 4},
    )
    assert r.status_code == 401


async def test_max_participants_must_be_power_of_two(client: AsyncClient):
    await register(client, "bob")
    token = await login(client, "bob")

    for bad in (3, 5, 6, 7, 0, 1):
        r = await client.post(
            "/api/tournaments/",
            json={"name": "Bad", "game_id": "rulixbots_v1", "max_participants": bad},
            headers=auth(token),
        )
        assert r.status_code == 422, f"Expected 422 for max_participants={bad}"


async def test_list_tournaments(client: AsyncClient):
    await register(client, "carol")
    token = await login(client, "carol")

    for name in ("Cup A", "Cup B"):
        await client.post(
            "/api/tournaments/",
            json={"name": name, "game_id": "rulixbots_v1", "max_participants": 2},
            headers=auth(token),
        )

    r = await client.get("/api/tournaments/")
    assert r.status_code == 200
    names = [t["name"] for t in r.json()]
    assert "Cup A" in names and "Cup B" in names


async def test_get_tournament_detail(client: AsyncClient):
    await register(client, "dan")
    token = await login(client, "dan")

    r = await client.post(
        "/api/tournaments/",
        json={"name": "Dan Cup", "game_id": "rulixbots_v1", "max_participants": 4},
        headers=auth(token),
    )
    t_id = r.json()["id"]

    r = await client.get(f"/api/tournaments/{t_id}")
    assert r.status_code == 200
    assert r.json()["total_rounds"] == 2  # log2(4) = 2
    assert r.json()["bracket"] == []  # no bracket until started


# ------------------------------------------------------------------ #
# Join                                                                #
# ------------------------------------------------------------------ #

async def test_join_tournament(client: AsyncClient):
    await register(client, "eve")
    token = await login(client, "eve")

    r = await client.post(
        "/api/tournaments/",
        json={"name": "Eve Cup", "game_id": "rulixbots_v1", "max_participants": 4},
        headers=auth(token),
    )
    t_id = r.json()["id"]

    r = await client.post(
        "/api/bots/",
        json={"game_id": "rulixbots_v1", "name": "EveBot", "code": '=> action = "wait"'},
        headers=auth(token),
    )
    bot_id = r.json()["id"]

    r = await client.post(f"/api/tournaments/{t_id}/join?bot_id={bot_id}", headers=auth(token))
    assert r.status_code == 201
    assert r.json()["participant_count"] == 1


async def test_cannot_join_twice(client: AsyncClient):
    await register(client, "frank")
    token = await login(client, "frank")

    r = await client.post(
        "/api/tournaments/",
        json={"name": "Frank Cup", "game_id": "rulixbots_v1", "max_participants": 4},
        headers=auth(token),
    )
    t_id = r.json()["id"]

    r = await client.post(
        "/api/bots/",
        json={"game_id": "rulixbots_v1", "name": "FrankBot", "code": '=> action = "wait"'},
        headers=auth(token),
    )
    bot_id = r.json()["id"]

    await client.post(f"/api/tournaments/{t_id}/join?bot_id={bot_id}", headers=auth(token))
    r = await client.post(f"/api/tournaments/{t_id}/join?bot_id={bot_id}", headers=auth(token))
    assert r.status_code == 400


async def test_cannot_start_with_one_participant(client: AsyncClient):
    await register(client, "grace")
    token = await login(client, "grace")

    r = await client.post(
        "/api/tournaments/",
        json={"name": "Grace Cup", "game_id": "rulixbots_v1", "max_participants": 4},
        headers=auth(token),
    )
    t_id = r.json()["id"]

    r = await client.post(
        "/api/bots/",
        json={"game_id": "rulixbots_v1", "name": "GraceBot", "code": '=> action = "wait"'},
        headers=auth(token),
    )
    bot_id = r.json()["id"]
    await client.post(f"/api/tournaments/{t_id}/join?bot_id={bot_id}", headers=auth(token))

    r = await client.post(f"/api/tournaments/{t_id}/start", headers=auth(token))
    assert r.status_code == 400


async def test_only_creator_can_start(client: AsyncClient):
    await register(client, "hank")
    token_h = await login(client, "hank")

    r = await client.post(
        "/api/tournaments/",
        json={"name": "Hank Cup", "game_id": "rulixbots_v1", "max_participants": 2},
        headers=auth(token_h),
    )
    t_id = r.json()["id"]

    # Hank joins
    r = await client.post(
        "/api/bots/",
        json={"game_id": "rulixbots_v1", "name": "HankBot", "code": '=> action = "wait"'},
        headers=auth(token_h),
    )
    await client.post(f"/api/tournaments/{t_id}/join?bot_id={r.json()['id']}", headers=auth(token_h))

    # Iris joins and tries to start
    await register(client, "iris")
    token_i = await login(client, "iris")
    r = await client.post(
        "/api/bots/",
        json={"game_id": "rulixbots_v1", "name": "IrisBot", "code": '=> action = "wait"'},
        headers=auth(token_i),
    )
    await client.post(f"/api/tournaments/{t_id}/join?bot_id={r.json()['id']}", headers=auth(token_i))

    r = await client.post(f"/api/tournaments/{t_id}/start", headers=auth(token_i))
    assert r.status_code == 403


# ------------------------------------------------------------------ #
# Full lifecycle — 2-player tournament (1 match = final)             #
# ------------------------------------------------------------------ #

async def test_two_player_tournament_completes(client: AsyncClient):
    await register(client, "jack")
    token_j = await login(client, "jack")

    await register(client, "kate")
    token_k = await login(client, "kate")

    r = await client.post(
        "/api/tournaments/",
        json={"name": "Duel", "game_id": "rulixbots_v1", "max_participants": 2},
        headers=auth(token_j),
    )
    t_id = r.json()["id"]

    for token, name in [(token_j, "Jack"), (token_k, "Kate")]:
        r = await client.post(
            "/api/bots/",
            json={"game_id": "rulixbots_v1", "name": name, "code": RUSHER_CODE},
            headers=auth(token),
        )
        bot_id = r.json()["id"]
        await client.post(f"/api/tournaments/{t_id}/join?bot_id={bot_id}", headers=auth(token))

    r = await client.post(f"/api/tournaments/{t_id}/start", headers=auth(token_j))
    assert r.status_code == 200
    assert r.json()["status"] == "active"

    t = await wait_for_tournament(client, t_id, token_j)
    assert t["status"] == "completed"
    assert t["winner_bot_id"] is not None
    assert t["winner_bot_name"] in ("Jack", "Kate")


async def test_two_player_tournament_bracket_has_one_match(client: AsyncClient):
    await register(client, "liam")
    token_l = await login(client, "liam")

    await register(client, "mia")
    token_m = await login(client, "mia")

    r = await client.post(
        "/api/tournaments/",
        json={"name": "Mini", "game_id": "rulixbots_v1", "max_participants": 2},
        headers=auth(token_l),
    )
    t_id = r.json()["id"]

    for token, name in [(token_l, "Liam"), (token_m, "Mia")]:
        r = await client.post(
            "/api/bots/",
            json={"game_id": "rulixbots_v1", "name": name, "code": RUSHER_CODE},
            headers=auth(token),
        )
        bot_id = r.json()["id"]
        await client.post(f"/api/tournaments/{t_id}/join?bot_id={bot_id}", headers=auth(token))

    await client.post(f"/api/tournaments/{t_id}/start", headers=auth(token_l))
    t = await wait_for_tournament(client, t_id, token_l)

    bracket = t["bracket"]
    assert len(bracket) == 1
    assert bracket[0]["round"] == 1
    assert bracket[0]["winner_bot_id"] is not None
    assert bracket[0]["match_id"] is not None


# ------------------------------------------------------------------ #
# Four-player tournament (2 rounds)                                   #
# ------------------------------------------------------------------ #

async def test_four_player_tournament_completes(client: AsyncClient):
    players = [("noah", "Noah"), ("olivia", "Olivia"), ("peter", "Peter"), ("quinn", "Quinn")]
    tokens = {}
    bot_ids = {}

    r = await client.post(
        "/api/auth/register",
        json={"username": players[0][0], "email": f"{players[0][0]}@test.com", "password": "pass1234"},
    )
    token_creator = (await client.post(
        "/api/auth/token", data={"username": players[0][0], "password": "pass1234"}
    )).json()["access_token"]

    r = await client.post(
        "/api/tournaments/",
        json={"name": "Grand Prix", "game_id": "rulixbots_v1", "max_participants": 4},
        headers=auth(token_creator),
    )
    t_id = r.json()["id"]

    for username, botname in players:
        if username != players[0][0]:
            await client.post(
                "/api/auth/register",
                json={"username": username, "email": f"{username}@test.com", "password": "pass1234"},
            )
        token = (await client.post(
            "/api/auth/token", data={"username": username, "password": "pass1234"}
        )).json()["access_token"]
        tokens[username] = token

        r = await client.post(
            "/api/bots/",
            json={"game_id": "rulixbots_v1", "name": botname, "code": RUSHER_CODE},
            headers=auth(token),
        )
        bot_id = r.json()["id"]
        bot_ids[username] = bot_id
        await client.post(f"/api/tournaments/{t_id}/join?bot_id={bot_id}", headers=auth(token))

    r = await client.post(f"/api/tournaments/{t_id}/start", headers=auth(token_creator))
    assert r.status_code == 200

    t = await wait_for_tournament(client, t_id, token_creator)
    assert t["status"] == "completed"
    assert t["winner_bot_id"] is not None
    assert t["total_rounds"] == 2

    # Bracket must have 3 matches: 2 in round 1, 1 final
    bracket = t["bracket"]
    assert len(bracket) == 3
    r1 = [m for m in bracket if m["round"] == 1]
    r2 = [m for m in bracket if m["round"] == 2]
    assert len(r1) == 2
    assert len(r2) == 1
    assert r2[0]["winner_bot_id"] is not None
