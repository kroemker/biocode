from datetime import datetime, timezone

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, WebSocket, WebSocketDisconnect
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_current_user
from app.core.game_runner import GameRunner
from app.database import SessionLocal, get_db
from app.games.registry import get_game
from app.models.bot import Bot
from app.models.match import Match, MatchPlayer
from app.models.rating import Rating
from app.models.user import User
from app.schemas.match import MatchOut, MatchReplay, MatchRequest, TestMatchRequest

router = APIRouter(prefix="/matches", tags=["matches"])

ELO_K = 32  # K-factor for Elo updates


# ------------------------------------------------------------------ #
# Background task: run the match and persist results                  #
# ------------------------------------------------------------------ #

async def _execute_match(match_id: int) -> None:
    async with SessionLocal() as db:
        match = await db.get(Match, match_id)
        if match is None:
            return

        try:
            match.status = "running"
            await db.commit()

            # Load ordered players
            result = await db.execute(
                select(MatchPlayer)
                .where(MatchPlayer.match_id == match_id)
                .order_by(MatchPlayer.player_index)
            )
            match_players = result.scalars().all()
            bots = [await db.get(Bot, mp.bot_id) for mp in match_players]

            game_module, factory = get_game(match.game_id)
            executors = [factory.create(bot.code) for bot in bots]

            runner = GameRunner()
            match_result = await runner.run(game_module, executors)

            match.status = "completed"
            match.winner_index = match_result.winner_index
            match.replay = match_result.snapshots
            match.completed_at = datetime.now(timezone.utc)
            await db.commit()

            # Update Elo ratings for both player bots (skip CPU/sample bots)
            await _update_ratings(db, match, bots, match_result.winner_index)

        except Exception:
            match.status = "error"
            await db.commit()
            raise


async def _update_ratings(db: AsyncSession, match: Match, bots: list[Bot], winner_index: int | None) -> None:
    """Apply Elo update for both players. Bots without a real owner are skipped."""
    if len(bots) != 2:
        return

    owner_ids = [bot.owner_id for bot in bots]

    ratings: list[Rating] = []
    for owner_id in owner_ids:
        result = await db.execute(
            select(Rating).where(Rating.user_id == owner_id, Rating.game_id == match.game_id)
        )
        rating = result.scalar_one_or_none()
        if rating is None:
            rating = Rating(user_id=owner_id, game_id=match.game_id)
            db.add(rating)
            await db.flush()
        ratings.append(rating)

    r0, r1 = ratings
    e0 = 1 / (1 + 10 ** ((r1.elo - r0.elo) / 400))
    e1 = 1 - e0

    if winner_index is None:  # draw
        s0, s1 = 0.5, 0.5
        r0.draws += 1
        r1.draws += 1
    elif winner_index == 0:
        s0, s1 = 1.0, 0.0
        r0.wins += 1
        r1.losses += 1
    else:
        s0, s1 = 0.0, 1.0
        r0.losses += 1
        r1.wins += 1

    r0.elo = round(r0.elo + ELO_K * (s0 - e0))
    r1.elo = round(r1.elo + ELO_K * (s1 - e1))
    await db.commit()


# ------------------------------------------------------------------ #
# Endpoints                                                           #
# ------------------------------------------------------------------ #

@router.post("/", response_model=MatchOut, status_code=201)
async def request_match(
    body: MatchRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # Validate challenger bot belongs to current user
    challenger = await db.get(Bot, body.bot_id)
    if challenger is None or challenger.owner_id != current_user.id:
        raise HTTPException(status_code=404, detail="Bot not found")
    if challenger.game_id != body.game_id:
        raise HTTPException(status_code=400, detail="Bot is not for this game")

    # Validate opponent bot is published
    opponent = await db.get(Bot, body.opponent_bot_id)
    if opponent is None or not opponent.is_published:
        raise HTTPException(status_code=404, detail="Opponent bot not found or not published")

    try:
        get_game(body.game_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="Game not found")

    match = Match(game_id=body.game_id, status="pending")
    db.add(match)
    await db.flush()
    db.add(MatchPlayer(match_id=match.id, player_index=0, bot_id=body.bot_id))
    db.add(MatchPlayer(match_id=match.id, player_index=1, bot_id=body.opponent_bot_id))
    await db.commit()
    await db.refresh(match)

    background_tasks.add_task(_execute_match, match.id)
    return match


@router.post("/test", response_model=MatchOut, status_code=201)
async def test_match(
    body: TestMatchRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Run the player's bot against a built-in sample bot. Unranked — no Elo change."""
    from app.games.rulixbots.sample_bots import SAMPLE_BOTS

    challenger = await db.get(Bot, body.bot_id)
    if challenger is None or challenger.owner_id != current_user.id:
        raise HTTPException(status_code=404, detail="Bot not found")

    try:
        game_module, _ = get_game(body.game_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="Game not found")

    # Find the requested sample bot
    sample = next((s for s in SAMPLE_BOTS if s[0] == body.sample_bot_name), None)
    if sample is None:
        names = [s[0] for s in SAMPLE_BOTS]
        raise HTTPException(status_code=404, detail=f"Sample bot not found. Available: {names}")

    # Create a temporary bot row for the sample bot (owner same as challenger for simplicity)
    cpu_bot = Bot(
        owner_id=current_user.id,
        game_id=body.game_id,
        name=f"CPU:{sample[0]}",
        code=sample[2],
        is_published=False,
    )
    db.add(cpu_bot)
    await db.flush()

    match = Match(game_id=body.game_id, status="pending")
    db.add(match)
    await db.flush()
    db.add(MatchPlayer(match_id=match.id, player_index=0, bot_id=challenger.id))
    db.add(MatchPlayer(match_id=match.id, player_index=1, bot_id=cpu_bot.id))
    await db.commit()
    await db.refresh(match)

    background_tasks.add_task(_execute_match_unranked, match.id)
    return match


async def _execute_match_unranked(match_id: int) -> None:
    """Same as _execute_match but skips Elo updates."""
    async with SessionLocal() as db:
        match = await db.get(Match, match_id)
        if match is None:
            return
        try:
            match.status = "running"
            await db.commit()

            result_rows = await db.execute(
                select(MatchPlayer)
                .where(MatchPlayer.match_id == match_id)
                .order_by(MatchPlayer.player_index)
            )
            match_players = result_rows.scalars().all()
            bots = [await db.get(Bot, mp.bot_id) for mp in match_players]

            game_module, factory = get_game(match.game_id)
            executors = [factory.create(bot.code) for bot in bots]

            runner = GameRunner()
            match_result = await runner.run(game_module, executors)

            match.status = "completed"
            match.winner_index = match_result.winner_index
            match.replay = match_result.snapshots
            match.completed_at = datetime.now(timezone.utc)
            await db.commit()
        except Exception:
            match.status = "error"
            await db.commit()
            raise


@router.get("/my", response_model=list[MatchOut])
async def list_my_matches(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Return all matches where the current user had a bot."""
    result = await db.execute(
        select(Match)
        .join(MatchPlayer, MatchPlayer.match_id == Match.id)
        .join(Bot, Bot.id == MatchPlayer.bot_id)
        .where(Bot.owner_id == current_user.id)
        .order_by(Match.created_at.desc())
    )
    return result.scalars().unique().all()


@router.get("/{match_id}", response_model=MatchReplay)
async def get_match(match_id: int, db: AsyncSession = Depends(get_db)):
    match = await db.get(Match, match_id)
    if match is None:
        raise HTTPException(status_code=404, detail="Match not found")
    return match


@router.websocket("/{match_id}/stream")
async def stream_match(match_id: int, websocket: WebSocket, db: AsyncSession = Depends(get_db)):
    """
    Stream match snapshots once the match completes.
    Sends: {"turn": int, "state": dict} per turn, then {"status": "completed", "winner": int|null}.
    Polls DB every 500 ms until the match finishes.
    """
    await websocket.accept()
    import asyncio
    try:
        for _ in range(120):  # up to 60 s
            match = await db.get(Match, match_id)
            if match is None:
                await websocket.send_json({"error": "match not found"})
                break
            if match.status == "completed" and match.replay:
                for turn, snapshot in enumerate(match.replay):
                    await websocket.send_json({"turn": turn, "state": snapshot})
                await websocket.send_json({"status": "completed", "winner": match.winner_index})
                break
            if match.status == "error":
                await websocket.send_json({"error": "match errored"})
                break
            await asyncio.sleep(0.5)
        else:
            await websocket.send_json({"error": "timeout waiting for match"})
    except WebSocketDisconnect:
        pass
    finally:
        await websocket.close()
