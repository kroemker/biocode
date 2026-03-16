from pydantic import BaseModel, field_validator


class TournamentCreate(BaseModel):
    name: str
    game_id: str
    max_participants: int  # must be 2, 4, 8, 16, or 32

    @field_validator("max_participants")
    @classmethod
    def must_be_power_of_two(cls, v: int) -> int:
        if v < 2 or (v & (v - 1)) != 0:
            raise ValueError("max_participants must be a power of 2 (2, 4, 8, 16, 32)")
        if v > 32:
            raise ValueError("max_participants cannot exceed 32")
        return v


class TournamentOut(BaseModel):
    id: int
    name: str
    game_id: str
    status: str
    max_participants: int
    created_by: int
    participant_count: int
    winner_bot_id: int | None
    winner_bot_name: str | None

    model_config = {"from_attributes": True}


class TournamentMatchOut(BaseModel):
    id: int
    round: int
    position: int
    bot1_id: int | None
    bot1_name: str | None
    bot2_id: int | None
    bot2_name: str | None
    match_id: int | None
    winner_bot_id: int | None
    is_bye: bool


class TournamentDetail(TournamentOut):
    total_rounds: int
    bracket: list[TournamentMatchOut]  # all matches, sorted by round then position
