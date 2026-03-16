"""
Built-in sample bots for RulixBots.

These are used for unranked test matches so players can try their code
before challenging other players.  Each entry is (name, description, code).
"""

SAMPLE_BOTS: list[tuple[str, str, str]] = [
    (
        "Rusher",
        "Charges straight at the enemy and attacks on sight.",
        """\
# ── Rusher ────────────────────────────────────────────────────────────────
# Closes the gap as fast as possible, then attacks.
# Attack fires whenever the enemy is adjacent (Chebyshev distance ≤ 1).

# Default: wait
=> action = "wait"

# Close horizontal gap
enemy_x > my_x => action = "move_e"
enemy_x < my_x => action = "move_w"

# Close vertical gap (only if already aligned horizontally)
enemy_x == my_x, enemy_y > my_y => action = "move_s"
enemy_x == my_x, enemy_y < my_y => action = "move_n"

# Attack overrides movement when adjacent
abs(enemy_x - my_x) <= 1, abs(enemy_y - my_y) <= 1 => action = "attack"
""",
    ),
    (
        "Cornerstone",
        "Retreats to a corner and attacks any enemy that gets close.",
        """\
# ── Cornerstone ───────────────────────────────────────────────────────────
# Runs to corner (0,0) and waits for the enemy to come within range.

=> action = "wait"

# Retreat to corner
my_x > 0 => action = "move_w"
my_x == 0, my_y > 0 => action = "move_n"

# Attack on sight
abs(enemy_x - my_x) <= 1, abs(enemy_y - my_y) <= 1 => action = "attack"
""",
    ),
    (
        "Wanderer",
        "Moves randomly by cycling through directions each turn.",
        """\
# ── Wanderer ──────────────────────────────────────────────────────────────
# Uses a simple turn-based counter to cycle through four directions.
# Demonstrates persistent bot memory across turns.

=> action = "wait"
=> dir = dir + 1
dir > 4 => dir = 1

dir == 1 => action = "move_n"
dir == 2 => action = "move_e"
dir == 3 => action = "move_s"
dir == 4 => action = "move_w"

# Always attack if adjacent, regardless of direction
abs(enemy_x - my_x) <= 1, abs(enemy_y - my_y) <= 1 => action = "attack"
""",
    ),
]
