from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.bot import Bot
from app.models.match import Match, MatchPlayer
from app.models.rating import Rating
from app.models.user import User
from app.schemas.bot import PublicBotOut
from app.schemas.match import MatchOut

router = APIRouter(prefix="/users", tags=["users"])


class RatingSummary(BaseModel):
    game_id: str
    elo: int
    wins: int
    losses: int
    draws: int


class UserProfile(BaseModel):
    id: int
    username: str
    ratings: list[RatingSummary]
    published_bots: list[PublicBotOut]


@router.get("/{username}", response_model=UserProfile)
async def get_profile(username: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.username == username))
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    ratings_result = await db.execute(
        select(Rating).where(Rating.user_id == user.id).order_by(Rating.elo.desc())
    )
    ratings = [
        RatingSummary(game_id=r.game_id, elo=r.elo, wins=r.wins, losses=r.losses, draws=r.draws)
        for r in ratings_result.scalars().all()
    ]

    bots_result = await db.execute(
        select(Bot).where(Bot.owner_id == user.id, Bot.is_published == True)  # noqa: E712
    )
    published_bots = [
        PublicBotOut(
            id=b.id,
            owner_id=b.owner_id,
            owner_username=user.username,
            game_id=b.game_id,
            name=b.name,
            version=b.version,
        )
        for b in bots_result.scalars().all()
    ]

    return UserProfile(id=user.id, username=user.username, ratings=ratings, published_bots=published_bots)


@router.get("/{username}/matches", response_model=list[MatchOut])
async def get_user_matches(username: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.username == username))
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    matches_result = await db.execute(
        select(Match)
        .join(MatchPlayer, MatchPlayer.match_id == Match.id)
        .join(Bot, Bot.id == MatchPlayer.bot_id)
        .where(Bot.owner_id == user.id)
        .order_by(Match.created_at.desc())
        .limit(50)
    )
    return matches_result.scalars().unique().all()
