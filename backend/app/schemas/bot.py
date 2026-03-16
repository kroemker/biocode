from pydantic import BaseModel


class BotCreate(BaseModel):
    game_id: str
    name: str
    code: str


class BotUpdate(BaseModel):
    name: str | None = None
    code: str | None = None


class BotOut(BaseModel):
    id: int
    owner_id: int
    game_id: str
    name: str
    version: int
    is_published: bool

    model_config = {"from_attributes": True}


class BotWithCode(BotOut):
    code: str
