from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Tournament(Base):
    __tablename__ = "tournaments"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    game_id: Mapped[str] = mapped_column(String(64), nullable=False)
    # registration | active | completed
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="registration")
    # Must be a power of 2; tournament starts when this many bots have joined
    max_participants: Mapped[int] = mapped_column(Integer, nullable=False)
    created_by: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    started_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    winner_bot_id: Mapped[int | None] = mapped_column(ForeignKey("bots.id"), nullable=True)

    participants: Mapped[list["TournamentParticipant"]] = relationship(
        back_populates="tournament", cascade="all, delete-orphan"
    )
    matches: Mapped[list["TournamentMatch"]] = relationship(
        back_populates="tournament", cascade="all, delete-orphan"
    )


class TournamentParticipant(Base):
    __tablename__ = "tournament_participants"
    __table_args__ = (UniqueConstraint("tournament_id", "bot_id"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    tournament_id: Mapped[int] = mapped_column(ForeignKey("tournaments.id"), nullable=False)
    bot_id: Mapped[int] = mapped_column(ForeignKey("bots.id"), nullable=False)
    seed: Mapped[int | None] = mapped_column(Integer, nullable=True)
    eliminated_round: Mapped[int | None] = mapped_column(Integer, nullable=True)

    tournament: Mapped["Tournament"] = relationship(back_populates="participants")
    bot: Mapped["Bot"] = relationship()


class TournamentMatch(Base):
    __tablename__ = "tournament_matches"

    id: Mapped[int] = mapped_column(primary_key=True)
    tournament_id: Mapped[int] = mapped_column(ForeignKey("tournaments.id"), nullable=False)
    round: Mapped[int] = mapped_column(Integer, nullable=False)
    position: Mapped[int] = mapped_column(Integer, nullable=False)
    bot1_id: Mapped[int | None] = mapped_column(ForeignKey("bots.id"), nullable=True)
    bot2_id: Mapped[int | None] = mapped_column(ForeignKey("bots.id"), nullable=True)
    match_id: Mapped[int | None] = mapped_column(ForeignKey("matches.id"), nullable=True)
    winner_bot_id: Mapped[int | None] = mapped_column(ForeignKey("bots.id"), nullable=True)
    is_bye: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    tournament: Mapped["Tournament"] = relationship(back_populates="matches")
    bot1: Mapped["Bot | None"] = relationship(foreign_keys=[bot1_id])
    bot2: Mapped["Bot | None"] = relationship(foreign_keys=[bot2_id])
    winner: Mapped["Bot | None"] = relationship(foreign_keys=[winner_bot_id])
