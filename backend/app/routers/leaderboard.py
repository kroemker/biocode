from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.games.registry import get_game
from app.models.rating import Rating
from app.models.user import User

router = APIRouter(prefix="/leaderboard", tags=["leaderboard"])


class LeaderboardEntry(BaseModel):
    rank: int
    user_id: int
    username: str
    elo: int
    wins: int
    losses: int
    draws: int


@router.get("/{game_id}", response_model=list[LeaderboardEntry])
async def get_leaderboard(game_id: str, db: AsyncSession = Depends(get_db)):
    try:
        get_game(game_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="Game not found")

    result = await db.execute(
        select(Rating, User)
        .join(User, User.id == Rating.user_id)
        .where(Rating.game_id == game_id)
        .order_by(Rating.elo.desc())
        .limit(100)
    )
    rows = result.all()
    return [
        LeaderboardEntry(
            rank=i + 1,
            user_id=user.id,
            username=user.username,
            elo=rating.elo,
            wins=rating.wins,
            losses=rating.losses,
            draws=rating.draws,
        )
        for i, (rating, user) in enumerate(rows)
    ]
