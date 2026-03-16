from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_current_user
from app.database import get_db
from app.models.bot import Bot
from app.models.user import User
from app.schemas.bot import BotCreate, BotOut, BotUpdate, BotWithCode

router = APIRouter(prefix="/bots", tags=["bots"])


@router.post("/", response_model=BotOut, status_code=status.HTTP_201_CREATED)
async def create_bot(
    body: BotCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    bot = Bot(owner_id=current_user.id, game_id=body.game_id, name=body.name, code=body.code)
    db.add(bot)
    await db.commit()
    await db.refresh(bot)
    return bot


@router.get("/", response_model=list[BotOut])
async def list_my_bots(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Bot).where(Bot.owner_id == current_user.id))
    return result.scalars().all()


@router.get("/{bot_id}", response_model=BotWithCode)
async def get_bot(
    bot_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    bot = await db.get(Bot, bot_id)
    if bot is None:
        raise HTTPException(status_code=404, detail="Bot not found")
    if bot.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not your bot")
    return bot


@router.patch("/{bot_id}", response_model=BotOut)
async def update_bot(
    bot_id: int,
    body: BotUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    bot = await db.get(Bot, bot_id)
    if bot is None:
        raise HTTPException(status_code=404, detail="Bot not found")
    if bot.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not your bot")

    if body.name is not None:
        bot.name = body.name
    if body.code is not None:
        bot.code = body.code
        bot.version += 1

    await db.commit()
    await db.refresh(bot)
    return bot


@router.post("/{bot_id}/publish", response_model=BotOut)
async def publish_bot(
    bot_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    bot = await db.get(Bot, bot_id)
    if bot is None:
        raise HTTPException(status_code=404, detail="Bot not found")
    if bot.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not your bot")

    bot.is_published = True
    await db.commit()
    await db.refresh(bot)
    return bot
