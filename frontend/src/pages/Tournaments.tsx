import { FormEvent, useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { games as gamesApi, tournaments as tournamentsApi } from "@/api/client";
import { useAuth } from "@/context/AuthContext";
import type { GameInfo, TournamentOut } from "@/types";

const STATUS_LABEL: Record<string, string> = {
  registration: "Open",
  active: "In Progress",
  completed: "Completed",
};

const STATUS_CLASS: Record<string, string> = {
  registration: "status-open",
  active: "status-active",
  completed: "status-done",
};

export function Tournaments() {
  const { user } = useAuth();
  const navigate = useNavigate();

  const [list, setList] = useState<TournamentOut[]>([]);
  const [games, setGames] = useState<GameInfo[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [showCreate, setShowCreate] = useState(false);

  // Create form state
  const [name, setName] = useState("");
  const [gameId, setGameId] = useState("");
  const [maxP, setMaxP] = useState(8);
  const [creating, setCreating] = useState(false);

  useEffect(() => {
    tournamentsApi.list().then(setList).catch((e) => setError(e.message));
    gamesApi.list().then((g) => { setGames(g); if (g.length > 0) setGameId(g[0].game_id); });
  }, []);

  async function handleCreate(e: FormEvent) {
    e.preventDefault();
    if (!name || !gameId) return;
    setCreating(true);
    setError(null);
    try {
      const t = await tournamentsApi.create(name, gameId, maxP);
      navigate(`/tournaments/${t.id}`);
    } catch (err) {
      setError((err as Error).message);
      setCreating(false);
    }
  }

  return (
    <main className="tournaments">
      <div className="page-header">
        <h1>Tournaments</h1>
        {user && (
          <button onClick={() => setShowCreate((v) => !v)}>
            {showCreate ? "Cancel" : "+ New tournament"}
          </button>
        )}
      </div>

      {showCreate && (
        <form onSubmit={handleCreate} className="create-tournament-form">
          <h2>Create tournament</h2>
          <label>
            Name
            <input value={name} onChange={(e) => setName(e.target.value)} required autoFocus />
          </label>
          <label>
            Game
            <select value={gameId} onChange={(e) => setGameId(e.target.value)}>
              {games.map((g) => (
                <option key={g.game_id} value={g.game_id}>{g.name}</option>
              ))}
            </select>
          </label>
          <label>
            Bracket size
            <select value={maxP} onChange={(e) => setMaxP(Number(e.target.value))}>
              {[2, 4, 8, 16].map((n) => (
                <option key={n} value={n}>{n} players</option>
              ))}
            </select>
          </label>
          {error && <p className="error">{error}</p>}
          <button type="submit" disabled={creating}>
            {creating ? "Creating…" : "Create"}
          </button>
        </form>
      )}

      {error && !showCreate && <p className="error">{error}</p>}

      {list.length === 0 && !error && <p>No tournaments yet.</p>}

      <div className="tournament-list">
        {list.map((t) => (
          <Link key={t.id} to={`/tournaments/${t.id}`} className="tournament-card">
            <div className="tc-top">
              <strong>{t.name}</strong>
              <span className={`status-badge ${STATUS_CLASS[t.status]}`}>
                {STATUS_LABEL[t.status]}
              </span>
            </div>
            <div className="tc-meta">
              {t.game_id} · {t.participant_count}/{t.max_participants} players
            </div>
            {t.winner_bot_name && (
              <div className="tc-winner">🏆 {t.winner_bot_name}</div>
            )}
          </Link>
        ))}
      </div>
    </main>
  );
}
