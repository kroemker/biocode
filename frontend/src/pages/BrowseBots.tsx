import { useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { bots as botsApi, games as gamesApi, matches as matchesApi } from "@/api/client";
import { useAuth } from "@/context/AuthContext";
import type { Bot, PublicBot } from "@/types";

export function BrowseBots() {
  const { gameId } = useParams<{ gameId: string }>();
  const { user } = useAuth();
  const navigate = useNavigate();

  const [published, setPublished] = useState<PublicBot[]>([]);
  const [myBots, setMyBots] = useState<Bot[]>([]);
  const [error, setError] = useState<string | null>(null);

  // Challenge modal state
  const [challenging, setChallenging] = useState<PublicBot | null>(null);
  const [selectedMyBot, setSelectedMyBot] = useState<number | null>(null);
  const [launching, setLaunching] = useState(false);

  useEffect(() => {
    if (!gameId) return;
    gamesApi
      .publishedBots(gameId)
      .then(setPublished)
      .catch((e) => setError(e.message));
  }, [gameId]);

  useEffect(() => {
    if (!user || !gameId) return;
    botsApi
      .list()
      .then((all) => {
        const mine = all.filter((b) => b.game_id === gameId);
        setMyBots(mine);
        if (mine.length > 0) setSelectedMyBot(mine[0].id);
      })
      .catch(() => {});
  }, [user, gameId]);

  function openChallenge(bot: PublicBot) {
    if (!user) { navigate("/login"); return; }
    setChallenging(bot);
  }

  async function confirmChallenge() {
    if (!challenging || !selectedMyBot || !gameId) return;
    setLaunching(true);
    setError(null);
    try {
      const match = await matchesApi.request(gameId, selectedMyBot, challenging.id);
      navigate(`/matches/${match.id}`);
    } catch (e) {
      setError((e as Error).message);
      setLaunching(false);
    }
  }

  return (
    <main className="browse-bots">
      <nav className="breadcrumb">
        <Link to="/games">Games</Link> /{" "}
        <Link to={`/games/${gameId}`}>{gameId}</Link> / Bots
      </nav>
      <h1>Published bots</h1>

      {error && <p className="error">{error}</p>}

      {published.length === 0 ? (
        <p>No published bots yet — be the first!</p>
      ) : (
        <table className="bots-table">
          <thead>
            <tr>
              <th>Bot</th>
              <th>Owner</th>
              <th>Version</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {published.map((bot) => (
              <tr key={bot.id}>
                <td><strong>{bot.name}</strong></td>
                <td>
                  <Link to={`/players/${bot.owner_username}`}>{bot.owner_username}</Link>
                </td>
                <td>v{bot.version}</td>
                <td>
                  {user && bot.owner_id !== user.id ? (
                    <button onClick={() => openChallenge(bot)}>Challenge</button>
                  ) : (
                    <span className="muted">{user && bot.owner_id === user.id ? "You" : "—"}</span>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}

      {/* Challenge modal */}
      {challenging && (
        <div className="modal-overlay" onClick={() => setChallenging(null)}>
          <div className="modal" onClick={(e) => e.stopPropagation()}>
            <h2>Challenge <em>{challenging.name}</em></h2>
            <p>
              by <Link to={`/players/${challenging.owner_username}`}>{challenging.owner_username}</Link>
            </p>
            <p>Pick which of your bots to send:</p>
            {myBots.length === 0 ? (
              <p className="error">
                You have no bots for this game.{" "}
                <Link to={`/bots/new/edit?game=${gameId}`}>Create one first.</Link>
              </p>
            ) : (
              <select
                value={selectedMyBot ?? ""}
                onChange={(e) => setSelectedMyBot(Number(e.target.value))}
              >
                {myBots.map((b) => (
                  <option key={b.id} value={b.id}>
                    {b.name} v{b.version}{b.is_published ? " (published)" : ""}
                  </option>
                ))}
              </select>
            )}
            {error && <p className="error">{error}</p>}
            <div className="modal-actions">
              <button onClick={() => setChallenging(null)} className="secondary">Cancel</button>
              <button onClick={confirmChallenge} disabled={launching || myBots.length === 0}>
                {launching ? "Starting…" : "▶ Start ranked match"}
              </button>
            </div>
          </div>
        </div>
      )}
    </main>
  );
}
