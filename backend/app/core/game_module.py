"""
Abstract base class every game must implement.

A GameModule is a pure, stateless object describing the rules of one game.
It never touches the database or HTTP — it only transforms game state dicts.
"""
from abc import ABC, abstractmethod
from typing import Any


class GameModule(ABC):
    # ------------------------------------------------------------------ #
    # Identity (implement as class-level attributes or properties)        #
    # ------------------------------------------------------------------ #

    @property
    @abstractmethod
    def game_id(self) -> str:
        """Unique, stable identifier, e.g. 'rulixbots_v1'."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Human-readable name shown in the UI."""

    @property
    @abstractmethod
    def description(self) -> str:
        """Short description shown in the game lobby."""

    @property
    @abstractmethod
    def player_count(self) -> int:
        """Number of players per match (usually 2)."""

    @property
    @abstractmethod
    def max_turns(self) -> int:
        """Match ends in a draw after this many turns."""

    # ------------------------------------------------------------------ #
    # Game logic                                                          #
    # ------------------------------------------------------------------ #

    @abstractmethod
    def create_state(self) -> dict[str, Any]:
        """Return the initial game state for a new match."""

    @abstractmethod
    def get_perception(self, state: dict[str, Any], player_index: int) -> dict[str, Any]:
        """
        Return the subset of state that bot[player_index] is allowed to see
        this turn. Perception is passed to the bot executor as input.
        """

    @abstractmethod
    def apply_action(
        self, state: dict[str, Any], player_index: int, action: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Apply an action from bot[player_index] and return the new state.
        Must not mutate the input state; return a new dict.
        """

    @abstractmethod
    def is_terminal(self, state: dict[str, Any]) -> bool:
        """Return True when the match is over (win or draw)."""

    @abstractmethod
    def get_winner(self, state: dict[str, Any]) -> int | None:
        """
        Return the winning player index (0-based), or None for a draw.
        Only called when is_terminal() is True.
        """

    @abstractmethod
    def validate_action(self, action: dict[str, Any]) -> bool:
        """
        Return True if the action dict is structurally valid.
        Called before apply_action; invalid actions are replaced with a
        default no-op to keep the match running.
        """

    def default_action(self, player_index: int) -> dict[str, Any]:
        """
        The action used when a bot times out or returns an invalid action.
        Override to provide a game-specific no-op. Default: empty dict.
        """
        return {}
