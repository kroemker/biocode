"""
RulixBots — a 10×10 grid combat game where bots are programmed in Rulix.

Grid:
  (0,0) is top-left, x increases east, y increases south.

Each turn a bot receives perception variables and must set the `action`
variable to one of: "move_n", "move_s", "move_e", "move_w", "attack", "wait".

Attack hits the enemy if they are within Chebyshev distance 1 (adjacent,
including diagonals) and deals ATTACK_DAMAGE health points.

The match ends immediately when either bot reaches 0 HP.  If max_turns is
reached with both bots alive the result is a draw.
"""
from copy import deepcopy
from typing import Any

from app.core.game_module import GameModule

GRID_SIZE = 10
INITIAL_HEALTH = 100
ATTACK_DAMAGE = 25
ATTACK_RANGE = 1          # Chebyshev distance (adjacent squares)
VALID_ACTIONS = {"move_n", "move_s", "move_e", "move_w", "attack", "wait"}


class RulixBotsModule(GameModule):

    @property
    def game_id(self) -> str:
        return "rulixbots_v1"

    @property
    def name(self) -> str:
        return "RulixBots"

    @property
    def description(self) -> str:
        return (
            "Program a bot in Rulix to fight on a 10×10 grid. "
            "Move toward your enemy, get adjacent, and attack. Last bot standing wins."
        )

    @property
    def player_count(self) -> int:
        return 2

    @property
    def max_turns(self) -> int:
        return 200

    # ------------------------------------------------------------------ #
    # State schema                                                        #
    # ------------------------------------------------------------------ #
    # {
    #   "turn": int,
    #   "grid_size": int,
    #   "bots": [
    #     {"x": int, "y": int, "health": int},   # player 0
    #     {"x": int, "y": int, "health": int},   # player 1
    #   ]
    # }

    def create_state(self) -> dict[str, Any]:
        return {
            "turn": 0,
            "grid_size": GRID_SIZE,
            "bots": [
                {"x": 2, "y": GRID_SIZE // 2, "health": INITIAL_HEALTH},
                {"x": GRID_SIZE - 3, "y": GRID_SIZE // 2, "health": INITIAL_HEALTH},
            ],
        }

    def get_perception(self, state: dict[str, Any], player_index: int) -> dict[str, Any]:
        me = state["bots"][player_index]
        enemy = state["bots"][1 - player_index]
        return {
            "my_x": me["x"],
            "my_y": me["y"],
            "my_health": me["health"],
            "enemy_x": enemy["x"],
            "enemy_y": enemy["y"],
            "enemy_health": enemy["health"],
            "turn": state["turn"],
            "grid_size": state["grid_size"],
        }

    def apply_action(
        self, state: dict[str, Any], player_index: int, action: dict[str, Any]
    ) -> dict[str, Any]:
        state = deepcopy(state)
        me = state["bots"][player_index]
        enemy = state["bots"][1 - player_index]
        act = action.get("action", "wait")

        if act == "move_n":
            me["y"] = max(0, me["y"] - 1)
        elif act == "move_s":
            me["y"] = min(state["grid_size"] - 1, me["y"] + 1)
        elif act == "move_w":
            me["x"] = max(0, me["x"] - 1)
        elif act == "move_e":
            me["x"] = min(state["grid_size"] - 1, me["x"] + 1)
        elif act == "attack":
            dx = abs(me["x"] - enemy["x"])
            dy = abs(me["y"] - enemy["y"])
            if max(dx, dy) <= ATTACK_RANGE:          # Chebyshev distance
                enemy["health"] = max(0, enemy["health"] - ATTACK_DAMAGE)

        # Advance turn counter after the last player acts each round
        if player_index == self.player_count - 1:
            state["turn"] += 1

        return state

    def is_terminal(self, state: dict[str, Any]) -> bool:
        return any(bot["health"] <= 0 for bot in state["bots"])

    def get_winner(self, state: dict[str, Any]) -> int | None:
        healths = [bot["health"] for bot in state["bots"]]
        if healths[0] <= 0 and healths[1] <= 0:
            return None  # simultaneous KO → draw
        if healths[0] <= 0:
            return 1
        if healths[1] <= 0:
            return 0
        return None  # max turns reached → draw

    def validate_action(self, action: dict[str, Any]) -> bool:
        return isinstance(action.get("action"), str) and action["action"] in VALID_ACTIONS

    def default_action(self, player_index: int) -> dict[str, Any]:
        return {"action": "wait"}
