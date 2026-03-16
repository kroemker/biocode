from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import auth, bots, games, leaderboard, matches, tournaments, users


@asynccontextmanager
async def lifespan(app: FastAPI):
    from app.games.rulixbots.module import RulixBotsModule
    from app.games.rulixbots.executor import RulixBotExecutorFactory
    from app.games.registry import register_game
    register_game(RulixBotsModule(), RulixBotExecutorFactory())
    yield


app = FastAPI(
    title="BotArena",
    description="Generic programming game platform",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Vite dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api")
app.include_router(games.router, prefix="/api")
app.include_router(bots.router, prefix="/api")
app.include_router(matches.router, prefix="/api")
app.include_router(leaderboard.router, prefix="/api")
app.include_router(users.router, prefix="/api")
app.include_router(tournaments.router, prefix="/api")


@app.get("/api/health")
async def health():
    return {"status": "ok"}
