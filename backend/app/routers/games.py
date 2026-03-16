from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.games.registry import get_game, list_games

router = APIRouter(prefix="/games", tags=["games"])


class GameInfo(BaseModel):
    game_id: str
    name: str
    description: str
    player_count: int
    max_turns: int


@router.get("/", response_model=list[GameInfo])
async def list_all_games():
    return [
        GameInfo(
            game_id=g.game_id,
            name=g.name,
            description=g.description,
            player_count=g.player_count,
            max_turns=g.max_turns,
        )
        for g in list_games()
    ]


@router.get("/{game_id}", response_model=GameInfo)
async def get_game_info(game_id: str):
    try:
        module, _ = get_game(game_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="Game not found")
    return GameInfo(
        game_id=module.game_id,
        name=module.name,
        description=module.description,
        player_count=module.player_count,
        max_turns=module.max_turns,
    )
