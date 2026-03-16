"""End-to-end tests for authentication endpoints."""
from httpx import AsyncClient

from tests.conftest import auth, login, register


async def test_register_creates_user(client: AsyncClient):
    data = await register(client, "alice")
    assert data["username"] == "alice"
    assert data["email"] == "alice@test.com"
    assert "id" in data
    assert "hashed_password" not in data


async def test_register_duplicate_username_rejected(client: AsyncClient):
    await register(client, "bob")
    r = await client.post(
        "/api/auth/register",
        json={"username": "bob", "email": "bob2@test.com", "password": "pass1234"},
    )
    assert r.status_code == 400
    assert "already taken" in r.json()["detail"]


async def test_register_duplicate_email_rejected(client: AsyncClient):
    await register(client, "carol")
    r = await client.post(
        "/api/auth/register",
        json={"username": "carol2", "email": "carol@test.com", "password": "pass1234"},
    )
    assert r.status_code == 400


async def test_login_returns_jwt(client: AsyncClient):
    await register(client, "dave")
    token = await login(client, "dave")
    assert isinstance(token, str)
    assert len(token) > 20


async def test_login_wrong_password_rejected(client: AsyncClient):
    await register(client, "eve")
    r = await client.post(
        "/api/auth/token",
        data={"username": "eve", "password": "wrongpassword"},
    )
    assert r.status_code == 401


async def test_login_unknown_user_rejected(client: AsyncClient):
    r = await client.post(
        "/api/auth/token",
        data={"username": "nobody", "password": "pass1234"},
    )
    assert r.status_code == 401


async def test_me_returns_current_user(client: AsyncClient):
    await register(client, "frank")
    token = await login(client, "frank")
    r = await client.get("/api/auth/me", headers=auth(token))
    assert r.status_code == 200
    assert r.json()["username"] == "frank"


async def test_me_without_token_rejected(client: AsyncClient):
    r = await client.get("/api/auth/me")
    assert r.status_code == 401
