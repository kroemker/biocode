# RulixBots — Game Rules & Bot API

## The Arena

Bots fight on a **10×10 grid**.  `(0, 0)` is the top-left corner.
`x` increases going **east**; `y` increases going **south**.

```
(0,0) ──────────────► x
  │   . . . . . . . . . .
  │   . . . . . . . . . .
  │   . B . . . . . E . .   ← starting row
  │   . . . . . . . . . .
  ▼
  y
```

Both bots start at health **100**.  The match ends when one (or both) bots
reach **0 HP**.  If neither bot is eliminated after **200 turns** the result
is a draw.

---

## Your Turn

Each turn your bot receives the following **read-only perception variables**
injected into its Rulix state:

| Variable | Type | Description |
|---|---|---|
| `my_x` | int | Your bot's column (0–9) |
| `my_y` | int | Your bot's row (0–9) |
| `my_health` | int | Your current HP (1–100) |
| `enemy_x` | int | Enemy column |
| `enemy_y` | int | Enemy row |
| `enemy_health` | int | Enemy current HP |
| `turn` | int | Current turn number (starts at 0) |
| `grid_size` | int | Always 10 |

To act, your bot must **set the `action` variable** before the cycle ends.
If your code never sets `action`, it defaults to `"wait"`.

| Value | Effect |
|---|---|
| `"move_n"` | Move one step north (y − 1) |
| `"move_s"` | Move one step south (y + 1) |
| `"move_e"` | Move one step east (x + 1) |
| `"move_w"` | Move one step west (x − 1) |
| `"attack"` | Attack the enemy if adjacent (Chebyshev distance ≤ 1) |
| `"wait"` | Do nothing |

Movement is clamped to the grid — you cannot walk off the edge.

---

## Combat

An **attack** deals **25 damage** if the enemy is within **Chebyshev distance 1**
(the 8 squares immediately surrounding you, including diagonals).
Attacking from further away does nothing.

Both bots act in turn order each round (player 0 first, then player 1).
A bot that is reduced to 0 HP mid-round can no longer act.

---

## Memory

Your bot's Rulix interpreter **persists its state between turns**.
Any variable you write that isn't a perception variable stays set on the next
turn.  Use this to implement counters, flags, and simple strategies.

```rulix
# Example: count the turns since last attack
=> turns_since_attack = turns_since_attack + 1
abs(enemy_x - my_x) <= 1, abs(enemy_y - my_y) <= 1 =>
    action = "attack"
    turns_since_attack = 0
```

---

## Rulix Quick Reference

```rulix
# Unconditional rule — runs every cycle
=> x = 1

# Conditional rule — runs only when ALL conditions are true
x > 0, x < 10 => print("in range")

# Block form
x > 5 =>
    y = x * 2
    z = y + 1

# disable — permanently prevents this rule from firing again
once => action = "move_e"  disable

# stop — halts the current cycle immediately
done == 1 => stop
```

Built-in functions available in bot code (sandbox preset):

| Group | Functions |
|---|---|
| Math | `abs()`, `min()`, `max()`, `floor()`, `sqrt()` |
| String | `len()`, `upper()`, `lower()`, `contains()`, `replace()` |
| Type | `is_null()`, `str()`, `int()`, `type()` |

`print()`, `log()`, `input()`, `delete()`, and `exists()` are **disabled** in bot code.

---

## Example Bot

```rulix
# Simple chaser: close the gap, then attack.

=> action = "wait"

enemy_x > my_x => action = "move_e"
enemy_x < my_x => action = "move_w"
enemy_x == my_x, enemy_y > my_y => action = "move_s"
enemy_x == my_x, enemy_y < my_y => action = "move_n"

# Attack overrides movement when adjacent
abs(enemy_x - my_x) <= 1, abs(enemy_y - my_y) <= 1 => action = "attack"
```
