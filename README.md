# BotArena

A browser-based platform where players write bots to compete in programming games. The platform is built as a generic framework — new games can be added with minimal effort while sharing all infrastructure: user accounts, matchmaking, Elo ratings, leaderboards, and tournaments.

The first game is **RulixBots**, where bots are written in [Rulix](https://github.com/kroemker/rulix), a lightweight rule-based scripting language.

---

## Features

- **In-browser bot editor** — Monaco editor with your bot's code, save and publish in one click
- **Test matches** — run your bot against built-in CPU opponents (unranked)
- **Ranked matches** — challenge any published bot, Elo updated automatically
- **Match replay viewer** — animated canvas replay with play/pause/step controls
- **Leaderboard** — per-game Elo rankings
- **Player profiles** — ratings, published bots, recent match history
- **Tournaments** — single-elimination brackets; create, join, start, watch live

---

## Tech stack

| Layer | Technology |
|---|---|
| Backend | Python 3.12, FastAPI, SQLAlchemy (async), PostgreSQL, Alembic |
| Frontend | React 18, TypeScript, Vite, Monaco Editor, React Router |
| Game engine | Custom `GameRunner` loop, abstract `GameModule` + `BotExecutor` interfaces |
| Auth | JWT (OAuth2 password flow) |
| Infra | Docker Compose |

---

## Getting started

### Prerequisites

- Docker and Docker Compose

### 1. Clone and configure

```bash
git clone <repo-url>
cd biocode
cp .env.example .env
# Edit .env — set a strong SECRET_KEY at minimum
```

### 2. Start all services

```bash
docker compose up --build
```

This starts:
- **PostgreSQL** on port 5432
- **Backend** (FastAPI + uvicorn) on port 8000
- **Frontend** (Vite dev server) on port 5173

### 3. Run database migrations

```bash
docker compose exec backend alembic upgrade head
```

### 4. Open the app

Navigate to **http://localhost:5173**

---

## Project structure

```
biocode/
├── backend/
│   ├── app/
│   │   ├── core/           # Auth, GameRunner, abstract interfaces
│   │   ├── games/
│   │   │   ├── registry.py
│   │   │   └── rulixbots/  # RulixBots game module + executor + sample bots
│   │   ├── models/         # SQLAlchemy models
│   │   ├── routers/        # FastAPI routers (auth, bots, matches, tournaments…)
│   │   └── schemas/        # Pydantic request/response schemas
│   └── alembic/            # Database migrations
└── frontend/
    └── src/
        ├── api/            # Typed API client
        ├── components/     # Bracket, CodeEditor, GameViewer
        ├── context/        # AuthContext
        ├── games/
        │   └── rulixbots/  # Canvas renderer
        └── pages/          # All page components
```

---

## API overview

| Method | Path | Description |
|---|---|---|
| POST | `/api/auth/register` | Register a new user |
| POST | `/api/auth/token` | Login (returns JWT) |
| GET | `/api/auth/me` | Current user info |
| GET | `/api/games/` | List all games |
| GET | `/api/games/{game_id}/bots` | Published bots for a game |
| GET | `/api/games/{game_id}/sample-bots` | Built-in CPU opponents |
| POST | `/api/bots/` | Create a bot |
| PATCH | `/api/bots/{id}` | Update bot code/name |
| POST | `/api/bots/{id}/publish` | Publish bot (makes it challengeable) |
| POST | `/api/matches/` | Start a ranked match |
| POST | `/api/matches/test` | Start an unranked test match vs CPU |
| GET | `/api/matches/{id}` | Get match + full replay |
| GET | `/api/matches/my` | Your match history |
| GET | `/api/leaderboard/{game_id}` | Top 100 players by Elo |
| GET | `/api/users/{username}` | Public player profile |
| GET | `/api/users/{username}/matches` | A player's recent matches |
| POST | `/api/tournaments/` | Create a tournament |
| GET | `/api/tournaments/` | List all tournaments |
| GET | `/api/tournaments/{id}` | Tournament detail + full bracket |
| POST | `/api/tournaments/{id}/join` | Join with a bot |
| POST | `/api/tournaments/{id}/start` | Start the tournament (creator only) |

---

## Adding a new game

1. Create `backend/app/games/<your_game>/module.py` implementing `GameModule`
2. Create `backend/app/games/<your_game>/executor.py` implementing `BotExecutor` + `BotExecutorFactory`
3. Register in `backend/app/main.py`:
   ```python
   register_game(YourGameModule(), YourExecutorFactory())
   ```
4. Add a canvas renderer in `frontend/src/games/<your_game>/renderer.ts`
5. Register the renderer in `frontend/src/pages/MatchViewer.tsx`

The rest of the platform (users, matches, Elo, tournaments, replays) works automatically.

---

## RulixBots

Bots fight on a **10×10 grid**. Both start at 100 HP. The match ends when a bot reaches 0 HP or after 200 turns (draw).

Each turn the bot receives read-only perception variables (`my_x`, `my_y`, `my_health`, `enemy_x`, `enemy_y`, `enemy_health`, `turn`, `grid_size`) and must set `action` to one of: `move_n`, `move_s`, `move_e`, `move_w`, `attack`, `wait`.

See [`backend/app/games/rulixbots/GAME_RULES.md`](backend/app/games/rulixbots/GAME_RULES.md) for the full rules and Rulix syntax reference.

**Example bot:**
```
# Move toward enemy, attack when adjacent
=> action = "wait"
enemy_x > my_x => action = "move_e"
enemy_x < my_x => action = "move_w"
enemy_y > my_y => action = "move_s"
enemy_y < my_y => action = "move_n"
abs(enemy_x - my_x) <= 1, abs(enemy_y - my_y) <= 1 => action = "attack"
```

Three sample bots are available for testing: **Rusher**, **Cornerstone**, and **Wanderer**.
