# BotArena — A Generic Programming Game Framework

## Vision

BotArena is a browser-based platform where players write code to control bots and compete against other players' bots. The platform is built as a **generic framework** so that new programming games can be added with minimal effort, while sharing all infrastructure: user accounts, matchmaking, leaderboards, tournaments, and the in-browser code editor.

The first game shipped on this platform is **RulixBots**, where players must write bots exclusively in [Rulix](https://github.com/kroemker/rulix) — a lightweight, rule-based scripting language. This constraint gives Rulix a fun showcase and creates a level playing field.

---

## Core Concepts

### Games
A **Game** is a self-contained module that defines:
- The rules and win conditions of a match
- How bot code is executed each turn
- What state is visible to a bot each turn (its "perception")
- What actions a bot can take
- A renderer that visualizes the match in the browser

The framework knows nothing about individual game logic — it only knows how to run a match given a game module.

### Bots
A **Bot** is a player's code submission for a specific game. Each bot is versioned: players can iterate on their code and publish new versions. Old versions are kept so match replays remain valid.

### Matches
A **Match** is a recorded confrontation between two (or more) bots. Matches are simulated server-side, and the full replay (state snapshots per turn) is stored so players can watch any match at any time.

### Leaderboards
Each game has its own leaderboard. Ratings are computed per-game using an Elo-style system updated after each ranked match.

### Tournaments
Tournaments are scheduled or on-demand brackets/round-robins within a game. They are first-class entities: the framework handles bracket generation, scheduling, and result tracking.

---

## User Flow

```
Register / Login
   └─> Choose a Game (e.g. RulixBots)
          ├─> Read game rules & API docs
          ├─> Write / edit bot code in the browser IDE
          ├─> Test bot vs. built-in sample bots (unranked)
          ├─> Publish bot (makes it available for ranked matches)
          ├─> Challenge another player's bot
          ├─> Watch match replay
          └─> View leaderboard / join tournament
```

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────┐
│                      Browser                        │
│  ┌──────────────┐  ┌──────────────┐  ┌───────────┐ │
│  │  Code Editor │  │ Game Viewer  │  │   Lobby   │ │
│  │  (Monaco)    │  │ (Canvas/SVG) │  │ Matches / │ │
│  └──────────────┘  └──────────────┘  │ Boards    │ │
│                                       └───────────┘ │
└──────────────────────┬──────────────────────────────┘
                       │  REST + WebSocket
┌──────────────────────▼──────────────────────────────┐
│                   API Server (Python)                │
│                                                     │
│  ┌────────────┐  ┌─────────────┐  ┌─────────────┐  │
│  │  Auth &    │  │  Match      │  │  Leaderboard│  │
│  │  Users     │  │  Scheduler  │  │  & Rankings │  │
│  └────────────┘  └──────┬──────┘  └─────────────┘  │
│                         │                           │
│               ┌─────────▼──────────┐                │
│               │   Game Runner      │                │
│               │  (pluggable per    │                │
│               │   game module)     │                │
│               └─────────┬──────────┘                │
│                         │                           │
│               ┌─────────▼──────────┐                │
│               │  Sandbox Executor  │                │
│               │  (runs bot code    │                │
│               │   in isolation)    │                │
│               └────────────────────┘                │
└──────────────────────┬──────────────────────────────┘
                       │
        ┌──────────────▼──────────────┐
        │        PostgreSQL           │
        │  users, bots, matches,      │
        │  replays, ratings, tourns   │
        └─────────────────────────────┘
```

---

## Game Module Interface

Each game is a Python module that implements the following interface:

```python
class GameModule:
    # Unique identifier, e.g. "rulixbots_v1"
    game_id: str

    # Human-readable name and description shown in the UI
    name: str
    description: str

    # Number of players per match (usually 2)
    player_count: int

    # Max turns before the match is declared a draw
    max_turns: int

    def create_state(self) -> dict:
        """Return the initial game state."""

    def get_perception(self, state: dict, player_index: int) -> dict:
        """Return what bot[player_index] can see this turn."""

    def apply_action(self, state: dict, player_index: int, action: dict) -> dict:
        """Apply an action from bot[player_index] and return the new state."""

    def is_terminal(self, state: dict) -> bool:
        """Return True if the match is over."""

    def get_winner(self, state: dict) -> int | None:
        """Return the winning player index, or None for a draw."""

    def validate_action(self, action: dict) -> bool:
        """Return True if the action dict is structurally valid."""
```

The framework's **Game Runner** calls these methods in a loop, calling each bot's code to produce an action, then advancing state. The runner is completely decoupled from game logic.

---

## First Game: RulixBots

**RulixBots** is a simple arena combat game where bots move and attack on a grid. Each turn, a bot receives its current perception (position, health, nearby enemies, etc.) as rulix variables and must output an action (move direction, attack, etc.) by setting a special output variable.

### Why Rulix?
- Rulix is intentionally limited: no loops, no recursion, just reactive rules
- This creates interesting strategic constraints and a level playing field
- Rulix programs are safe to sandbox (no file I/O, no network access)
- The embedded Python API (`RulixInterpreter`) makes server-side execution easy

### Bot Execution Model
1. Server injects perception data as pre-set variables into the interpreter
2. Bot's rulix program runs for one cycle
3. Server reads the output variable to get the bot's action
4. Interpreter state persists across turns (bots can maintain memory)

### Sandboxing
- Each bot runs in an isolated subprocess with a CPU time limit (e.g. 50ms/turn)
- Rulix's `RulixConfig.sandbox()` preset restricts built-ins to type/math/string only
- No file system or network access is permitted

---

## Tech Stack

See [TECH_STACK.md](./TECH_STACK.md) for the full rationale and decision.

| Layer | Choice |
|---|---|
| Backend API | Python + FastAPI |
| Bot Execution | Python subprocess + Rulix interpreter |
| Database | PostgreSQL |
| Real-time | WebSockets (via FastAPI) |
| Frontend | React + TypeScript |
| Code Editor | Monaco Editor |
| Game Renderer | HTML5 Canvas (per game) |
| Auth | JWT (access + refresh tokens) |
| Deployment | Docker Compose |

---

## Extensibility Checklist

To add a new game to the platform, a developer only needs to:

- [ ] Write a `GameModule` subclass implementing the interface above
- [ ] Write a frontend renderer (a React component receiving state snapshots)
- [ ] Write documentation / API reference for bot authors
- [ ] Register the module in the game registry

No changes to the core framework (auth, matchmaking, leaderboard, tournament engine) are needed.

---

## Roadmap

### Phase 1 — Foundation
- [ ] User auth (register, login, JWT)
- [ ] Generic match runner + replay storage
- [ ] RulixBots game module
- [ ] In-browser Rulix editor with syntax highlighting
- [ ] Unranked test matches vs. built-in bots
- [ ] Match replay viewer

### Phase 2 — Competition
- [ ] Ranked matchmaking (Elo ratings)
- [ ] Leaderboard per game
- [ ] Player profiles & bot version history
- [ ] Challenge system (send challenge to specific player)

### Phase 3 — Tournaments
- [ ] Tournament creation (bracket / round-robin)
- [ ] Automated scheduling & result tracking
- [ ] Tournament leaderboards

### Phase 4 — Platform Growth
- [ ] Add a second game (opens the generic framework to the community)
- [ ] Public bot code sharing (optional per player)
- [ ] Spectator mode (watch live matches via WebSocket)
