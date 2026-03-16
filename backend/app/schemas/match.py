from typing import Any
from pydantic import BaseModel


class MatchRequest(BaseModel):
    game_id: str
    bot_id: int          # challenger's bot
    opponent_bot_id: int  # target bot


class TestMatchRequest(BaseModel):
    game_id: str
    bot_id: int
    sample_bot_name: str  # e.g. "Rusher"


class MatchOut(BaseModel):
    id: int
    game_id: str
    status: str
    winner_index: int | None

    model_config = {"from_attributes": True}


class MatchReplay(MatchOut):
    replay: list[Any] | None
