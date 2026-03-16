"""
Sandbox executor: runs a single bot for one turn in an isolated subprocess.

The executor injects the perception dict as variables, runs the bot code,
and reads back the action variable. Each call is stateless from the
framework's perspective; the bot's own interpreter state is managed by
the concrete executor subclass.
"""
from abc import ABC, abstractmethod
from typing import Any


class BotExecutor(ABC):
    """
    One executor instance lives for the duration of a match and is owned
    by the GameRunner. It maintains whatever per-bot state is needed
    (e.g. a persistent interpreter instance) between turns.
    """

    @abstractmethod
    def get_action(
        self,
        perception: dict[str, Any],
        timeout_ms: int = 100,
    ) -> dict[str, Any]:
        """
        Run the bot for one turn.

        - Inject *perception* as input variables.
        - Execute bot code under *timeout_ms* budget.
        - Return the action dict produced by the bot.
        - Return an empty dict on timeout or error (never raise).
        """

    @abstractmethod
    def close(self) -> None:
        """Release any resources held by this executor."""


class BotExecutorFactory(ABC):
    """Creates BotExecutor instances for a specific language/runtime."""

    @abstractmethod
    def create(self, code: str) -> BotExecutor:
        """Return a fresh executor loaded with *code*."""
