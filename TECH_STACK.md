# Tech Stack Decisions

## Backend: Python + FastAPI

**Choice:** Python with [FastAPI](https://fastapi.tiangolo.com/)

**Rationale:**
- Rulix is a Python program. The backend must be Python to embed `RulixInterpreter` directly — no inter-process bridge needed for the executor.
- FastAPI is async-native, which pairs well with WebSockets (live match streaming, spectator mode).
- FastAPI's automatic OpenAPI docs make the API self-documenting from day one.
- Pydantic models (built into FastAPI) provide clean request/response validation.
- Lightweight compared to Django; we don't need an ORM or admin panel out of the box.

**Alternatives considered:**
- *Django*: Too heavy; admin panel and ORM aren't needed in Phase 1.
- *Node.js*: Would require a Python subprocess bridge just to run Rulix — unnecessary complexity.

---

## Database: PostgreSQL

**Choice:** [PostgreSQL](https://www.postgresql.org/) with [SQLAlchemy](https://www.sqlalchemy.org/) (async via `asyncpg`)

**Rationale:**
- Relational model fits the domain well: users, bots, matches, ratings are naturally normalized.
- JSONB columns handle semi-structured data (match replays, game state snapshots) without a separate document store.
- Excellent support for window functions (useful for Elo rating calculations and leaderboard queries).
- SQLAlchemy async provides type-safe queries and easy migrations via Alembic.

**Alternatives considered:**
- *MongoDB*: JSONB in Postgres covers the document use-case without splitting the data tier.
- *SQLite*: Fine for development but not suitable for concurrent production workloads.

---

## Bot Execution: Sandboxed Subprocess

**Choice:** Isolated Python subprocess per match tick, using `RulixConfig.sandbox()`

**Rationale:**
- Rulix's built-in sandbox (`RulixConfig.sandbox()`) already restricts available functions to type/math/string.
- Running each bot in a subprocess with `resource` limits (CPU time, memory) provides OS-level isolation.
- Timeouts are enforced by killing the subprocess if it exceeds the per-turn time budget.
- This approach is simple, auditable, and requires no container runtime for Phase 1.

**Future hardening:**
- Move to Docker-based execution (one container per match) when the platform scales.
- Consider `seccomp` profiles or `nsjail` for stricter syscall filtering.

---

## Real-time: WebSockets (FastAPI)

**Choice:** Native WebSocket support in FastAPI

**Rationale:**
- Match replays can be streamed turn-by-turn to the browser as they are simulated.
- Spectator mode (Phase 4) requires server-push; WebSockets are the right primitive.
- FastAPI handles WebSocket connections natively — no additional library needed.

**Alternatives considered:**
- *Server-Sent Events (SSE)*: Simpler but unidirectional; doesn't support future interactive features.
- *Socket.IO*: Heavier abstraction; FastAPI's native WebSocket is sufficient.

---

## Frontend: React + TypeScript

**Choice:** [React](https://react.dev/) with [TypeScript](https://www.typescriptlang.org/), bundled with [Vite](https://vitejs.dev/)

**Rationale:**
- React's component model is a natural fit: the code editor, game viewer, and lobby are independent, composable components.
- TypeScript catches integration bugs between frontend and the API early (especially important for game state shape contracts).
- Vite provides fast development builds and HMR.
- Large ecosystem: Monaco Editor, routing (React Router), state management (Zustand or React Query) are all well-supported.

**Alternatives considered:**
- *Vue*: Valid choice, but React has broader ecosystem support for Monaco and Canvas-heavy apps.
- *SvelteKit*: Appealing for performance, but smaller ecosystem for the specialized components needed here.

---

## Code Editor: Monaco Editor

**Choice:** [Monaco Editor](https://microsoft.github.io/monaco-editor/) (the editor behind VS Code)

**Rationale:**
- Supports custom language grammars: we can add Rulix syntax highlighting and basic autocompletion.
- Familiar UX for developers.
- Works well inside a React component via `@monaco-editor/react`.

---

## Game Renderer: HTML5 Canvas (per game)

**Choice:** Each game provides its own React component that renders to an HTML5 `<canvas>`

**Rationale:**
- Games have very different visual styles; a generic renderer would be overly constraining.
- Canvas is performant for 2D game-style animations (grid movement, health bars, etc.).
- The framework only requires the renderer to accept a stream of state snapshots — no other coupling.

**Alternatives considered:**
- *WebGL / Three.js*: Overkill for the initial 2D grid game; can be used by future game modules.
- *SVG*: Fine for simple games but less performant for animations with many elements.

---

## Authentication: JWT

**Choice:** JWT with short-lived access tokens + long-lived refresh tokens, stored in `httpOnly` cookies

**Rationale:**
- Stateless access tokens integrate cleanly with FastAPI's dependency injection for route protection.
- `httpOnly` cookies prevent XSS-based token theft.
- Refresh token rotation allows sessions to stay alive without permanent credentials in localStorage.

---

## Deployment: Docker Compose

**Choice:** Docker Compose for local development and initial production deployment

**Rationale:**
- Keeps the entire stack (API, database, frontend dev server) reproducible in one command.
- The bot sandbox subprocess runs inside the API container in Phase 1; easy to extract to a separate container later.
- Simple enough for a solo or small team project without requiring Kubernetes.

**Production path:**
- A single VPS running Docker Compose is sufficient for Phase 1–2.
- When match volume grows, the executor service can be extracted and scaled independently.

---

## Summary Table

| Layer | Technology | Key Reason |
|---|---|---|
| API framework | FastAPI (Python) | Native Rulix embedding, async WebSocket |
| ORM / migrations | SQLAlchemy async + Alembic | Type-safe, async-ready |
| Database | PostgreSQL | Relational + JSONB for replays |
| Bot sandbox | Python subprocess + RulixConfig.sandbox() | Simple, auditable isolation |
| Real-time | FastAPI WebSocket | Built-in, no extra dependencies |
| Frontend | React + TypeScript + Vite | Component model, type safety, ecosystem |
| Code editor | Monaco Editor | VS Code UX, custom language support |
| Game renderer | HTML5 Canvas (per game) | Flexible, performant, decoupled |
| Auth | JWT in httpOnly cookies | Stateless, XSS-safe |
| Deployment | Docker Compose | Simple, reproducible |
