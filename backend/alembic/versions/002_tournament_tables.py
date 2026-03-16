"""tournament tables

Revision ID: 002
Revises: 001
Create Date: 2026-03-16
"""
import sqlalchemy as sa
from alembic import op

revision = "002"
down_revision = "001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "tournaments",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(128), nullable=False),
        sa.Column("game_id", sa.String(64), nullable=False),
        sa.Column("status", sa.String(16), nullable=False),
        sa.Column("max_participants", sa.Integer(), nullable=False),
        sa.Column("created_by", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=True),
        sa.Column("started_at", sa.DateTime(), nullable=True),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.Column("winner_bot_id", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"]),
        sa.ForeignKeyConstraint(["winner_bot_id"], ["bots.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "tournament_participants",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("tournament_id", sa.Integer(), nullable=False),
        sa.Column("bot_id", sa.Integer(), nullable=False),
        sa.Column("seed", sa.Integer(), nullable=True),
        sa.Column("eliminated_round", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(["tournament_id"], ["tournaments.id"]),
        sa.ForeignKeyConstraint(["bot_id"], ["bots.id"]),
        sa.UniqueConstraint("tournament_id", "bot_id"),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "tournament_matches",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("tournament_id", sa.Integer(), nullable=False),
        sa.Column("round", sa.Integer(), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("bot1_id", sa.Integer(), nullable=True),
        sa.Column("bot2_id", sa.Integer(), nullable=True),
        sa.Column("match_id", sa.Integer(), nullable=True),
        sa.Column("winner_bot_id", sa.Integer(), nullable=True),
        sa.Column("is_bye", sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(["tournament_id"], ["tournaments.id"]),
        sa.ForeignKeyConstraint(["bot1_id"], ["bots.id"]),
        sa.ForeignKeyConstraint(["bot2_id"], ["bots.id"]),
        sa.ForeignKeyConstraint(["match_id"], ["matches.id"]),
        sa.ForeignKeyConstraint(["winner_bot_id"], ["bots.id"]),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("tournament_matches")
    op.drop_table("tournament_participants")
    op.drop_table("tournaments")
