"""
GameRunner: the match simulation loop.

This is the heart of the framework. It is completely decoupled from any
specific game — it only calls the GameModule interface and delegates bot
execution to BotExecutor instances.
"""
from copy import deepcopy
from dataclasses import dataclass, field
from typing import Any

from app.core.game_module import GameModule
from app.core.sandbox import BotExecutor


@dataclass
class MatchResult:
    winner_index: int | None  # None = draw
    snapshots: list[dict[str, Any]] = field(default_factory=list)
    turns_played: int = 0
    error: str | None = None


class GameRunner:
    """
    Runs a single match to completion and returns a MatchResult.

    Usage:
        runner = GameRunner()
        result = await runner.run(game_module, [executor_a, executor_b])
    """

    async def run(
        self,
        game: GameModule,
        executors: list[BotExecutor],
        turn_timeout_ms: int = 100,
    ) -> MatchResult:
        assert len(executors) == game.player_count, (
            f"Expected {game.player_count} executors, got {len(executors)}"
        )

        state = game.create_state()
        snapshots: list[dict[str, Any]] = [deepcopy(state)]

        for turn in range(game.max_turns):
            if game.is_terminal(state):
                break

            for player_index, executor in enumerate(executors):
                if game.is_terminal(state):
                    break

                perception = game.get_perception(state, player_index)
                action = executor.get_action(perception, timeout_ms=turn_timeout_ms)

                if not game.validate_action(action):
                    action = game.default_action(player_index)

                state = game.apply_action(state, player_index, action)

            snapshots.append(deepcopy(state))

        for executor in executors:
            executor.close()

        return MatchResult(
            winner_index=game.get_winner(state) if game.is_terminal(state) else None,
            snapshots=snapshots,
            turns_played=len(snapshots) - 1,
        )
