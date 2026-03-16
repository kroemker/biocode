"""
RulixBots BotExecutor — runs a player's Rulix code for one turn.

Execution model
---------------
One RulixBotExecutor instance is created per bot per match and lives for the
duration of the match.  The underlying RulixInterpreter is reused across turns
so that bot-owned state variables (memory) persist between turns — this is an
intentional game mechanic.

Before each turn the framework injects perception variables into the
interpreter's state, resets `action` to "wait", and runs the bot's code for
one cycle.  After the cycle the executor reads back the `action` variable and
returns it as the bot's chosen action.

Safety
------
- RulixConfig.sandbox() restricts available built-ins to type, math, and
  string functions.  I/O and state-manipulation functions are disabled.
- Rulix has no loops or recursion, so a single cycle always terminates in
  O(rules) time.  A thread-based timeout is included as a safety net against
  pathological programs (e.g. enormous numbers of rules).
- On any error (RulixError, timeout, unexpected exception) the executor logs
  the failure and returns the default "wait" action so the match continues.
"""
import concurrent.futures
import logging
from typing import Any

from rulix import RulixConfig, RulixError, RulixInterpreter

from app.core.sandbox import BotExecutor, BotExecutorFactory

log = logging.getLogger(__name__)

# Maximum wall-clock time (seconds) allowed for a single turn execution.
# Rulix programs are O(rules) and have no loops, so this is purely a
# safety net and should never be hit in practice.
_TURN_TIMEOUT_S = 0.5


class RulixBotExecutor(BotExecutor):
    """Executes one Rulix bot for the lifetime of a single match."""

    def __init__(self, code: str) -> None:
        config = RulixConfig.sandbox()
        self._interpreter = RulixInterpreter(config=config)
        self._code = code
        self._timed_out = False   # once poisoned, always return default action

    # ------------------------------------------------------------------ #
    # BotExecutor interface                                               #
    # ------------------------------------------------------------------ #

    def get_action(
        self,
        perception: dict[str, Any],
        timeout_ms: int = 100,
    ) -> dict[str, Any]:
        if self._timed_out:
            return {"action": "wait"}

        # Inject this turn's perception as state variables
        for key, value in perception.items():
            self._interpreter.state.set(key, value)

        # Ensure action defaults to "wait" if the bot never sets it
        self._interpreter.state.set("action", "wait")

        timeout_s = max(timeout_ms / 1000.0, _TURN_TIMEOUT_S)
        try:
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
                future = pool.submit(self._interpreter.run, self._code)
                future.result(timeout=timeout_s)
        except concurrent.futures.TimeoutError:
            # Mark poisoned: the background thread may still be mutating
            # interpreter state, so we stop reusing this interpreter.
            self._timed_out = True
            log.warning("Rulix bot timed out after %.3fs", timeout_s)
            return {"action": "wait"}
        except RulixError as exc:
            log.debug("Rulix runtime error: %s", exc)
            return {"action": "wait"}
        except Exception as exc:
            log.warning("Unexpected error in Rulix executor: %s", exc)
            return {"action": "wait"}

        action = self._interpreter.state.get("action", "wait")
        return {"action": action}

    def close(self) -> None:
        # Nothing to release — interpreter holds only in-memory state
        pass


class RulixBotExecutorFactory(BotExecutorFactory):
    """Creates a fresh RulixBotExecutor for each bot slot in a match."""

    def create(self, code: str) -> RulixBotExecutor:
        return RulixBotExecutor(code)
