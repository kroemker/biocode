from datetime import datetime
from typing import Any
from sqlalchemy import DateTime, ForeignKey, Integer, JSON, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Match(Base):
    __tablename__ = "matches"

    id: Mapped[int] = mapped_column(primary_key=True)
    game_id: Mapped[str] = mapped_column(String(64), nullable=False)
    # pending | running | completed | error
    status: Mapped[str] = mapped_column(String(16), default="pending")
    winner_index: Mapped[int | None] = mapped_column(Integer, nullable=True)
    # list of state snapshots, one per turn
    replay: Mapped[list[Any] | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    players: Mapped[list["MatchPlayer"]] = relationship(back_populates="match")


class MatchPlayer(Base):
    __tablename__ = "match_players"

    id: Mapped[int] = mapped_column(primary_key=True)
    match_id: Mapped[int] = mapped_column(ForeignKey("matches.id"), nullable=False)
    player_index: Mapped[int] = mapped_column(Integer, nullable=False)
    bot_id: Mapped[int] = mapped_column(ForeignKey("bots.id"), nullable=False)

    match: Mapped["Match"] = relationship(back_populates="players")
    bot: Mapped["Bot"] = relationship(back_populates="match_players")
