import { useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { bots as botsApi, games as gamesApi, matches as matchesApi } from "@/api/client";
import { useAuth } from "@/context/AuthContext";
import type { Bot, GameInfo, Match, SampleBot } from "@/types";

export function GameLobby() {
  const { gameId } = useParams<{ gameId: string }>();
  const { user } = useAuth();
  const navigate = useNavigate();

  const [game, setGame] = useState<GameInfo | null>(null);
  const [myBots, setMyBots] = useState<Bot[]>([]);
  const [sampleBots, setSampleBots] = useState<SampleBot[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [selectedBotId, setSelectedBotId] = useState<number | null>(null);
  const [selectedSample, setSelectedSample] = useState<string>("");
  const [starting, setStarting] = useState(false);

  useEffect(() => {
    if (!gameId) return;
    Promise.all([
      gamesApi.get(gameId),
      gamesApi.sampleBots(gameId),
    ])
      .then(([g, samples]) => {
        setGame(g);
        setSampleBots(samples);
        if (samples.length > 0) setSelectedSample(samples[0].name);
      })
      .catch((e) => setError(e.message));
  }, [gameId]);

  useEffect(() => {
    if (!user) return;
    botsApi
      .list()
      .then((all) => {
        const forThisGame = all.filter((b) => b.game_id === gameId);
        setMyBots(forThisGame);
        if (forThisGame.length > 0) setSelectedBotId(forThisGame[0].id);
      })
      .catch((e) => setError(e.message));
  }, [user, gameId]);

  async function handleTestMatch() {
    if (!selectedBotId || !selectedSample || !gameId) return;
    setError(null);
    setStarting(true);
    try {
      const match = await matchesApi.test(gameId, selectedBotId, selectedSample);
      navigate(`/matches/${match.id}`);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setStarting(false);
    }
  }

  if (!game) return <p>Loading…</p>;

  return (
    <main className="game-lobby">
      <nav className="breadcrumb">
        <Link to="/games">Games</Link> / {game.name}
      </nav>

      <h1>{game.name}</h1>
      <p className="game-desc">{game.description}</p>
      <p className="game-meta">
        {game.player_count} players · up to {game.max_turns} turns
      </p>

      {error && <p className="error">{error}</p>}

      {user ? (
        <section className="lobby-section">
          <h2>Your bots</h2>
          {myBots.length === 0 ? (
            <p>You have no bots for this game yet.</p>
          ) : (
            <ul className="bot-list">
              {myBots.map((bot) => (
                <li key={bot.id} className={`bot-item ${selectedBotId === bot.id ? "selected" : ""}`}>
                  <button className="bot-select-btn" onClick={() => setSelectedBotId(bot.id)}>
                    <strong>{bot.name}</strong>
                    <span className="bot-meta">v{bot.version} {bot.is_published ? "· published" : ""}</span>
                  </button>
                  <Link to={`/bots/${bot.id}/edit`} className="edit-link">Edit</Link>
                </li>
              ))}
            </ul>
          )}
          <Link to={`/bots/new/edit?game=${gameId}`} className="button-link">
            + New bot
          </Link>

          {myBots.length > 0 && sampleBots.length > 0 && (
            <div className="test-match-box">
              <h3>Test match</h3>
              <p>Run your bot against a built-in opponent. Unranked — no Elo change.</p>
              <div className="test-match-controls">
                <select value={selectedSample} onChange={(e) => setSelectedSample(e.target.value)}>
                  {sampleBots.map((s) => (
                    <option key={s.name} value={s.name}>
                      {s.name} — {s.description}
                    </option>
                  ))}
                </select>
                <button onClick={handleTestMatch} disabled={starting || !selectedBotId}>
                  {starting ? "Starting…" : "▶ Start test match"}
                </button>
              </div>
            </div>
          )}
        </section>
      ) : (
        <p>
          <Link to="/login">Sign in</Link> to create a bot and play.
        </p>
      )}

      <section className="lobby-section">
        <h2>Challenge players</h2>
        <p>Browse all published bots and start a ranked match.</p>
        <Link to={`/games/${gameId}/bots`} className="button-link" style={{ marginTop: 8, display: "inline-block" }}>
          Browse bots →
        </Link>
      </section>

      <section className="lobby-section">
        <h2>Leaderboard</h2>
        <Link to={`/leaderboard/${gameId}`}>View full leaderboard →</Link>
      </section>
    </main>
  );
}
