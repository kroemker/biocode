from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_current_user
from app.database import get_db
from app.models.match import Match, MatchPlayer
from app.models.user import User
from app.schemas.match import MatchOut, MatchReplay, MatchRequest

router = APIRouter(prefix="/matches", tags=["matches"])


@router.post("/", response_model=MatchOut, status_code=201)
async def request_match(
    body: MatchRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # TODO: validate bots exist and belong to correct players, enqueue match
    match = Match(game_id=body.game_id, status="pending")
    db.add(match)
    await db.flush()

    db.add(MatchPlayer(match_id=match.id, player_index=0, bot_id=body.bot_id))
    db.add(MatchPlayer(match_id=match.id, player_index=1, bot_id=body.opponent_bot_id))

    await db.commit()
    await db.refresh(match)
    return match


@router.get("/{match_id}", response_model=MatchReplay)
async def get_match(match_id: int, db: AsyncSession = Depends(get_db)):
    match = await db.get(Match, match_id)
    if match is None:
        raise HTTPException(status_code=404, detail="Match not found")
    return match


@router.websocket("/{match_id}/stream")
async def stream_match(match_id: int, websocket: WebSocket, db: AsyncSession = Depends(get_db)):
    """
    Stream match snapshots turn-by-turn as the match runs.
    Sends JSON messages: {"turn": int, "state": dict} per turn,
    then {"status": "completed", "winner": int|null} when done.
    """
    await websocket.accept()
    # TODO: subscribe to match progress events and forward snapshots
    try:
        await websocket.send_json({"error": "streaming not yet implemented"})
    except WebSocketDisconnect:
        pass
    finally:
        await websocket.close()
