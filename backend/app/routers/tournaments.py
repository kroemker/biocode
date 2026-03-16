import math
import random
from datetime import datetime, timezone

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_current_user
from app.core.game_runner import GameRunner
from app.database import SessionLocal, get_db
from app.games.registry import get_game
from app.models.bot import Bot
from app.models.match import Match, MatchPlayer
from app.models.tournament import Tournament, TournamentMatch, TournamentParticipant
from app.models.user import User
from app.schemas.tournament import TournamentCreate, TournamentDetail, TournamentMatchOut, TournamentOut

router = APIRouter(prefix="/tournaments", tags=["tournaments"])


# ------------------------------------------------------------------ #
# Helpers                                                             #
# ------------------------------------------------------------------ #

def _total_rounds(max_participants: int) -> int:
    return int(math.log2(max_participants))


def _to_out(t: Tournament, participant_count: int) -> TournamentOut:
    return TournamentOut(
        id=t.id,
        name=t.name,
        game_id=t.game_id,
        status=t.status,
        max_participants=t.max_participants,
        created_by=t.created_by,
        participant_count=participant_count,
        winner_bot_id=t.winner_bot_id,
        winner_bot_name=t.winner.name if t.winner_bot_id and hasattr(t, "winner") and t.winner else None,
    )


def _match_to_out(tm: TournamentMatch) -> TournamentMatchOut:
    return TournamentMatchOut(
        id=tm.id,
        round=tm.round,
        position=tm.position,
        bot1_id=tm.bot1_id,
        bot1_name=tm.bot1.name if tm.bot1 else None,
        bot2_id=tm.bot2_id,
        bot2_name=tm.bot2.name if tm.bot2 else None,
        match_id=tm.match_id,
        winner_bot_id=tm.winner_bot_id,
        is_bye=tm.is_bye,
    )


# ------------------------------------------------------------------ #
# Background task: run entire tournament sequentially                 #
# ------------------------------------------------------------------ #

async def _run_tournament(tournament_id: int) -> None:
    async with SessionLocal() as db:
        tournament = await db.get(Tournament, tournament_id)
        if tournament is None:
            return

        game_module, factory = get_game(tournament.game_id)
        runner = GameRunner()
        total_rounds = _total_rounds(tournament.max_participants)

        for round_num in range(1, total_rounds + 1):
            result = await db.execute(
                select(TournamentMatch)
                .where(
                    TournamentMatch.tournament_id == tournament_id,
                    TournamentMatch.round == round_num,
                )
                .order_by(TournamentMatch.position)
            )
            t_matches = result.scalars().all()

            for tm in t_matches:
                # Refresh to pick up bot ids set by previous rounds
                await db.refresh(tm)

                if tm.is_bye:
                    tm.winner_bot_id = tm.bot1_id
                    await db.commit()
                    continue

                if tm.bot1_id is None or tm.bot2_id is None:
                    # Shouldn't happen in normal flow, but guard
                    continue

                bot1 = await db.get(Bot, tm.bot1_id)
                bot2 = await db.get(Bot, tm.bot2_id)

                match = Match(game_id=tournament.game_id, status="running")
                db.add(match)
                await db.flush()
                db.add(MatchPlayer(match_id=match.id, player_index=0, bot_id=bot1.id))
                db.add(MatchPlayer(match_id=match.id, player_index=1, bot_id=bot2.id))
                tm.match_id = match.id
                await db.commit()

                executors = [factory.create(bot1.code), factory.create(bot2.code)]
                try:
                    match_result = await runner.run(game_module, executors)
                    match.status = "completed"
                    match.winner_index = match_result.winner_index
                    match.replay = match_result.snapshots
                    match.completed_at = datetime.now(timezone.utc)

                    if match_result.winner_index == 0:
                        tm.winner_bot_id = bot1.id
                    elif match_result.winner_index == 1:
                        tm.winner_bot_id = bot2.id
                    else:
                        # Draw — bot1 advances (seed advantage)
                        tm.winner_bot_id = bot1.id
                except Exception:
                    match.status = "error"
                    tm.winner_bot_id = bot1.id  # default advance on error
                finally:
                    await db.commit()

            # Propagate winners to next round
            if round_num < total_rounds:
                next_result = await db.execute(
                    select(TournamentMatch)
                    .where(
                        TournamentMatch.tournament_id == tournament_id,
                        TournamentMatch.round == round_num + 1,
                    )
                    .order_by(TournamentMatch.position)
                )
                next_matches = next_result.scalars().all()
                for i, next_tm in enumerate(next_matches):
                    left = t_matches[i * 2]
                    right = t_matches[i * 2 + 1]
                    next_tm.bot1_id = left.winner_bot_id
                    next_tm.bot2_id = right.winner_bot_id
                await db.commit()

        # Mark eliminated participants
        for round_num in range(1, total_rounds + 1):
            result = await db.execute(
                select(TournamentMatch)
                .where(
                    TournamentMatch.tournament_id == tournament_id,
                    TournamentMatch.round == round_num,
                )
            )
            for tm in result.scalars().all():
                loser_id = None
                if tm.winner_bot_id == tm.bot1_id:
                    loser_id = tm.bot2_id
                elif tm.winner_bot_id == tm.bot2_id:
                    loser_id = tm.bot1_id
                if loser_id:
                    elim_result = await db.execute(
                        select(TournamentParticipant).where(
                            TournamentParticipant.tournament_id == tournament_id,
                            TournamentParticipant.bot_id == loser_id,
                        )
                    )
                    participant = elim_result.scalar_one_or_none()
                    if participant:
                        participant.eliminated_round = round_num
            await db.commit()

        # Find winner from final match
        final_result = await db.execute(
            select(TournamentMatch).where(
                TournamentMatch.tournament_id == tournament_id,
                TournamentMatch.round == total_rounds,
                TournamentMatch.position == 0,
            )
        )
        final_match = final_result.scalar_one_or_none()

        tournament.status = "completed"
        tournament.winner_bot_id = final_match.winner_bot_id if final_match else None
        tournament.completed_at = datetime.now(timezone.utc)
        await db.commit()


# ------------------------------------------------------------------ #
# Endpoints                                                           #
# ------------------------------------------------------------------ #

@router.post("/", response_model=TournamentOut, status_code=201)
async def create_tournament(
    body: TournamentCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        get_game(body.game_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="Game not found")

    t = Tournament(
        name=body.name,
        game_id=body.game_id,
        status="registration",
        max_participants=body.max_participants,
        created_by=current_user.id,
    )
    db.add(t)
    await db.commit()
    await db.refresh(t)
    return TournamentOut(
        id=t.id, name=t.name, game_id=t.game_id, status=t.status,
        max_participants=t.max_participants, created_by=t.created_by,
        participant_count=0, winner_bot_id=None, winner_bot_name=None,
    )


@router.get("/", response_model=list[TournamentOut])
async def list_tournaments(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Tournament).order_by(Tournament.created_at.desc()).limit(50)
    )
    tournaments = result.scalars().all()
    out = []
    for t in tournaments:
        count_result = await db.execute(
            select(TournamentParticipant).where(TournamentParticipant.tournament_id == t.id)
        )
        count = len(count_result.scalars().all())

        winner_name: str | None = None
        if t.winner_bot_id:
            wb = await db.get(Bot, t.winner_bot_id)
            winner_name = wb.name if wb else None

        out.append(TournamentOut(
            id=t.id, name=t.name, game_id=t.game_id, status=t.status,
            max_participants=t.max_participants, created_by=t.created_by,
            participant_count=count, winner_bot_id=t.winner_bot_id,
            winner_bot_name=winner_name,
        ))
    return out


@router.get("/{tournament_id}", response_model=TournamentDetail)
async def get_tournament(tournament_id: int, db: AsyncSession = Depends(get_db)):
    t = await db.get(Tournament, tournament_id)
    if t is None:
        raise HTTPException(status_code=404, detail="Tournament not found")

    participants_result = await db.execute(
        select(TournamentParticipant).where(TournamentParticipant.tournament_id == tournament_id)
    )
    participant_count = len(participants_result.scalars().all())

    matches_result = await db.execute(
        select(TournamentMatch)
        .where(TournamentMatch.tournament_id == tournament_id)
        .order_by(TournamentMatch.round, TournamentMatch.position)
    )
    t_matches = matches_result.scalars().all()

    # Eagerly load bot names
    bracket: list[TournamentMatchOut] = []
    for tm in t_matches:
        b1 = await db.get(Bot, tm.bot1_id) if tm.bot1_id else None
        b2 = await db.get(Bot, tm.bot2_id) if tm.bot2_id else None
        bracket.append(TournamentMatchOut(
            id=tm.id,
            round=tm.round,
            position=tm.position,
            bot1_id=tm.bot1_id,
            bot1_name=b1.name if b1 else None,
            bot2_id=tm.bot2_id,
            bot2_name=b2.name if b2 else None,
            match_id=tm.match_id,
            winner_bot_id=tm.winner_bot_id,
            is_bye=tm.is_bye,
        ))

    winner_name: str | None = None
    if t.winner_bot_id:
        wb = await db.get(Bot, t.winner_bot_id)
        winner_name = wb.name if wb else None

    return TournamentDetail(
        id=t.id, name=t.name, game_id=t.game_id, status=t.status,
        max_participants=t.max_participants, created_by=t.created_by,
        participant_count=participant_count,
        winner_bot_id=t.winner_bot_id, winner_bot_name=winner_name,
        total_rounds=_total_rounds(t.max_participants),
        bracket=bracket,
    )


@router.post("/{tournament_id}/join", response_model=TournamentOut, status_code=201)
async def join_tournament(
    tournament_id: int,
    bot_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    t = await db.get(Tournament, tournament_id)
    if t is None:
        raise HTTPException(status_code=404, detail="Tournament not found")
    if t.status != "registration":
        raise HTTPException(status_code=400, detail="Tournament is not accepting registrations")

    bot = await db.get(Bot, bot_id)
    if bot is None or bot.owner_id != current_user.id:
        raise HTTPException(status_code=404, detail="Bot not found")
    if bot.game_id != t.game_id:
        raise HTTPException(status_code=400, detail="Bot is for the wrong game")

    # Count current participants
    count_result = await db.execute(
        select(TournamentParticipant).where(TournamentParticipant.tournament_id == tournament_id)
    )
    participants = count_result.scalars().all()

    # Check user doesn't already have a bot in this tournament
    existing_bot_ids = {p.bot_id for p in participants}
    # Check if user already entered any bot
    user_bots_result = await db.execute(
        select(Bot).where(Bot.owner_id == current_user.id, Bot.game_id == t.game_id)
    )
    user_bot_ids = {b.id for b in user_bots_result.scalars().all()}
    if user_bot_ids & existing_bot_ids:
        raise HTTPException(status_code=400, detail="You already have a bot in this tournament")

    if len(participants) >= t.max_participants:
        raise HTTPException(status_code=400, detail="Tournament is full")

    db.add(TournamentParticipant(tournament_id=tournament_id, bot_id=bot_id))
    await db.commit()

    return TournamentOut(
        id=t.id, name=t.name, game_id=t.game_id, status=t.status,
        max_participants=t.max_participants, created_by=t.created_by,
        participant_count=len(participants) + 1,
        winner_bot_id=t.winner_bot_id, winner_bot_name=None,
    )


@router.post("/{tournament_id}/start", response_model=TournamentOut)
async def start_tournament(
    tournament_id: int,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    t = await db.get(Tournament, tournament_id)
    if t is None:
        raise HTTPException(status_code=404, detail="Tournament not found")
    if t.created_by != current_user.id:
        raise HTTPException(status_code=403, detail="Only the creator can start the tournament")
    if t.status != "registration":
        raise HTTPException(status_code=400, detail="Tournament already started or completed")

    participants_result = await db.execute(
        select(TournamentParticipant).where(TournamentParticipant.tournament_id == tournament_id)
    )
    participants = participants_result.scalars().all()
    if len(participants) < 2:
        raise HTTPException(status_code=400, detail="Need at least 2 participants to start")

    # Shuffle and seed participants
    shuffled = list(participants)
    random.shuffle(shuffled)
    for i, p in enumerate(shuffled):
        p.seed = i + 1
    await db.flush()

    # Determine bracket size (next power of 2 >= len(participants), max = max_participants)
    n = len(shuffled)
    bracket_size = 1
    while bracket_size < n:
        bracket_size *= 2

    # Pad with None bots for byes
    bot_ids: list[int | None] = [p.bot_id for p in shuffled] + [None] * (bracket_size - n)
    total_rounds = int(math.log2(bracket_size))

    # Create round 1 match slots
    for pos in range(bracket_size // 2):
        b1 = bot_ids[pos * 2]
        b2 = bot_ids[pos * 2 + 1]
        is_bye = b2 is None
        db.add(TournamentMatch(
            tournament_id=tournament_id,
            round=1,
            position=pos,
            bot1_id=b1,
            bot2_id=b2,
            is_bye=is_bye,
        ))

    # Create empty slots for rounds 2..total_rounds
    for round_num in range(2, total_rounds + 1):
        for pos in range(bracket_size // (2 ** round_num)):
            db.add(TournamentMatch(
                tournament_id=tournament_id,
                round=round_num,
                position=pos,
                is_bye=False,
            ))

    t.status = "active"
    t.started_at = datetime.now(timezone.utc)
    await db.commit()

    background_tasks.add_task(_run_tournament, tournament_id)

    return TournamentOut(
        id=t.id, name=t.name, game_id=t.game_id, status=t.status,
        max_participants=t.max_participants, created_by=t.created_by,
        participant_count=n, winner_bot_id=None, winner_bot_name=None,
    )
