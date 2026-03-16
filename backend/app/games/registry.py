"""
Game registry: the single source of truth for all installed games.

To add a new game:
  1. Implement GameModule and BotExecutorFactory for your game.
  2. Import and register them here with register_game().
"""
from app.core.game_module import GameModule
from app.core.sandbox import BotExecutorFactory

_games: dict[str, tuple[GameModule, BotExecutorFactory]] = {}


def register_game(module: GameModule, factory: BotExecutorFactory) -> None:
    _games[module.game_id] = (module, factory)


def get_game(game_id: str) -> tuple[GameModule, BotExecutorFactory]:
    if game_id not in _games:
        raise KeyError(f"Unknown game: {game_id!r}")
    return _games[game_id]


def list_games() -> list[GameModule]:
    return [module for module, _ in _games.values()]
