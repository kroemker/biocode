"""
Test configuration.

Uses an in-memory SQLite database so tests run without a real PostgreSQL
instance.  Each test function gets a freshly created schema (create_all /
drop_all) via the `client` fixture.

Background tasks (match execution, tournament runner) reference `SessionLocal`
directly inside their module namespace.  We patch those references before
building the httpx client so they hit the same test database.
"""
import asyncio

import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

import app.routers.matches as matches_module
import app.routers.tournaments as tournaments_module
from app.database import Base, get_db
from app.games.registry import _games, register_game
from app.games.rulixbots.executor import RulixBotExecutorFactory
from app.games.rulixbots.module import RulixBotsModule
from app.main import app

TEST_DB_URL = "sqlite+aiosqlite:///:memory:"


@pytest_asyncio.fixture
async def client():
    engine = create_async_engine(
        TEST_DB_URL,
        connect_args={"check_same_thread": False},
    )
    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    # Create schema
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Patch SessionLocal used directly by background-task functions
    original_matches_sl = matches_module.SessionLocal
    original_tournaments_sl = tournaments_module.SessionLocal
    matches_module.SessionLocal = session_factory
    tournaments_module.SessionLocal = session_factory

    # Register game (normally done in the lifespan handler)
    _games.clear()
    register_game(RulixBotsModule(), RulixBotExecutorFactory())

    # Override get_db FastAPI dependency
    async def override_get_db():
        async with session_factory() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as c:
        yield c

    # Tear down
    app.dependency_overrides.clear()
    matches_module.SessionLocal = original_matches_sl
    tournaments_module.SessionLocal = original_tournaments_sl

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


# ------------------------------------------------------------------ #
# Shared helpers available to all test modules                        #
# ------------------------------------------------------------------ #

async def register(client: AsyncClient, username: str, password: str = "pass1234") -> dict:
    r = await client.post(
        "/api/auth/register",
        json={"username": username, "email": f"{username}@test.com", "password": password},
    )
    assert r.status_code == 201, r.text
    return r.json()


async def login(client: AsyncClient, username: str, password: str = "pass1234") -> str:
    r = await client.post(
        "/api/auth/token",
        data={"username": username, "password": password},
    )
    assert r.status_code == 200, r.text
    return r.json()["access_token"]


def auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


async def create_and_publish_bot(
    client: AsyncClient,
    token: str,
    game_id: str = "rulixbots_v1",
    name: str = "TestBot",
    code: str = '=> action = "wait"',
) -> dict:
    r = await client.post(
        "/api/bots/",
        json={"game_id": game_id, "name": name, "code": code},
        headers=auth(token),
    )
    assert r.status_code == 201, r.text
    bot = r.json()
    r = await client.post(f"/api/bots/{bot['id']}/publish", headers=auth(token))
    assert r.status_code == 200, r.text
    return r.json()


async def wait_for_match(client: AsyncClient, match_id: int, token: str, attempts: int = 40) -> dict:
    """Poll until the match reaches a terminal state."""
    for _ in range(attempts):
        r = await client.get(f"/api/matches/{match_id}", headers=auth(token))
        data = r.json()
        if data["status"] in ("completed", "error"):
            return data
        await asyncio.sleep(0.1)
    raise TimeoutError(f"Match {match_id} did not complete in time")


async def wait_for_tournament(
    client: AsyncClient, tournament_id: int, token: str, attempts: int = 60
) -> dict:
    """Poll until the tournament reaches completed state."""
    for _ in range(attempts):
        r = await client.get(f"/api/tournaments/{tournament_id}", headers=auth(token))
        data = r.json()
        if data["status"] == "completed":
            return data
        await asyncio.sleep(0.2)
    raise TimeoutError(f"Tournament {tournament_id} did not complete in time")
