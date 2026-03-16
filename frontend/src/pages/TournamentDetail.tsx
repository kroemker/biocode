import { useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { bots as botsApi, tournaments as tournamentsApi } from "@/api/client";
import { Bracket } from "@/components/Bracket/Bracket";
import { useAuth } from "@/context/AuthContext";
import type { Bot, TournamentDetail as TDetail } from "@/types";

const POLL_INTERVAL_MS = 2000;

export function TournamentDetail() {
  const { tournamentId } = useParams<{ tournamentId: string }>();
  const { user } = useAuth();
  const navigate = useNavigate();

  const [tournament, setTournament] = useState<TDetail | null>(null);
  const [myBots, setMyBots] = useState<Bot[]>([]);
  const [selectedBot, setSelectedBot] = useState<number | null>(null);
  const [joining, setJoining] = useState(false);
  const [starting, setStarting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Load (and poll while active)
  useEffect(() => {
    if (!tournamentId) return;
    let cancelled = false;

    async function load() {
      try {
        const t = await tournamentsApi.get(Number(tournamentId));
        if (cancelled) return;
        setTournament(t);
        if (t.status === "active") {
          setTimeout(load, POLL_INTERVAL_MS);
        }
      } catch (e) {
        if (!cancelled) setError((e as Error).message);
      }
    }

    load();
    return () => { cancelled = true; };
  }, [tournamentId]);

  // Load user's bots for this game
  useEffect(() => {
    if (!user || !tournament) return;
    botsApi.list().then((all) => {
      const mine = all.filter((b) => b.game_id === tournament.game_id);
      setMyBots(mine);
      if (mine.length > 0) setSelectedBot(mine[0].id);
    });
  }, [user, tournament?.game_id]);

  async function handleJoin() {
    if (!selectedBot || !tournamentId) return;
    setError(null);
    setJoining(true);
    try {
      await tournamentsApi.join(Number(tournamentId), selectedBot);
      const t = await tournamentsApi.get(Number(tournamentId));
      setTournament(t);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setJoining(false);
    }
  }

  async function handleStart() {
    if (!tournamentId) return;
    setError(null);
    setStarting(true);
    try {
      await tournamentsApi.start(Number(tournamentId));
      const t = await tournamentsApi.get(Number(tournamentId));
      setTournament(t);
    } catch (e) {
      setError((e as Error).message);
      setStarting(false);
    }
  }

  if (error && !tournament) return <main><p className="error">{error}</p></main>;
  if (!tournament) return <main><p>Loading…</p></main>;

  const isCreator = user?.id === tournament.created_by;
  const isFull = tournament.participant_count >= tournament.max_participants;
  const alreadyIn = false; // Could compute from participant list if exposed

  return (
    <main className="tournament-detail">
      <nav className="breadcrumb">
        <Link to="/tournaments">Tournaments</Link> / {tournament.name}
      </nav>

      <div className="td-header">
        <div>
          <h1>{tournament.name}</h1>
          <p className="game-meta">
            {tournament.game_id} · {tournament.participant_count}/{tournament.max_participants} players ·{" "}
            <span className={`status-badge ${tournament.status === "registration" ? "status-open" : tournament.status === "active" ? "status-active" : "status-done"}`}>
              {tournament.status === "registration" ? "Open" : tournament.status === "active" ? "In Progress" : "Completed"}
            </span>
          </p>
        </div>

        <div className="td-actions">
          {error && <span className="error">{error}</span>}
          {tournament.status === "registration" && user && !isCreator && !isFull && (
            <div className="join-row">
              {myBots.length === 0 ? (
                <span className="muted">No bots for this game. <Link to={`/bots/new/edit?game=${tournament.game_id}`}>Create one.</Link></span>
              ) : (
                <>
                  <select value={selectedBot ?? ""} onChange={(e) => setSelectedBot(Number(e.target.value))}>
                    {myBots.map((b) => (
                      <option key={b.id} value={b.id}>{b.name} v{b.version}</option>
                    ))}
                  </select>
                  <button onClick={handleJoin} disabled={joining}>
                    {joining ? "Joining…" : "Join tournament"}
                  </button>
                </>
              )}
            </div>
          )}
          {tournament.status === "registration" && isCreator && tournament.participant_count >= 2 && (
            <button onClick={handleStart} disabled={starting}>
              {starting ? "Starting…" : "▶ Start tournament"}
            </button>
          )}
          {tournament.status === "registration" && isCreator && tournament.participant_count < 2 && (
            <span className="muted">Need at least 2 participants to start</span>
          )}
          {isFull && tournament.status === "registration" && !isCreator && (
            <span className="muted">Tournament is full</span>
          )}
        </div>
      </div>

      {tournament.winner_bot_name && (
        <div className="tournament-winner">
          🏆 Winner: <strong>{tournament.winner_bot_name}</strong>
        </div>
      )}

      {tournament.bracket.length > 0 ? (
        <div className="bracket-container">
          <Bracket bracket={tournament.bracket} totalRounds={tournament.total_rounds} />
        </div>
      ) : (
        <p className="muted" style={{ marginTop: 24 }}>
          Bracket will appear once the tournament starts.
        </p>
      )}
    </main>
  );
}
