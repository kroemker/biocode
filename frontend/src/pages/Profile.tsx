import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { users as usersApi } from "@/api/client";
import { useAuth } from "@/context/AuthContext";
import type { Match, UserProfile } from "@/types";

export function Profile() {
  const { username } = useParams<{ username: string }>();
  const { user: me } = useAuth();
  const [profile, setProfile] = useState<UserProfile | null>(null);
  const [matches, setMatches] = useState<Match[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!username) return;
    Promise.all([usersApi.profile(username), usersApi.matches(username)])
      .then(([p, m]) => {
        setProfile(p);
        setMatches(m);
      })
      .catch((e) => setError(e.message));
  }, [username]);

  if (error) return <main><p className="error">{error}</p></main>;
  if (!profile) return <main><p>Loading…</p></main>;

  const isMe = me?.username === username;

  return (
    <main className="profile">
      <h1>
        {profile.username}
        {isMe && <span className="badge" style={{ marginLeft: 10 }}>You</span>}
      </h1>

      {profile.ratings.length > 0 && (
        <section>
          <h2>Ratings</h2>
          <table className="leaderboard-table">
            <thead>
              <tr>
                <th>Game</th>
                <th>Elo</th>
                <th>W</th>
                <th>L</th>
                <th>D</th>
              </tr>
            </thead>
            <tbody>
              {profile.ratings.map((r) => (
                <tr key={r.game_id}>
                  <td><Link to={`/games/${r.game_id}`}>{r.game_id}</Link></td>
                  <td><strong>{r.elo}</strong></td>
                  <td className="win">{r.wins}</td>
                  <td className="loss">{r.losses}</td>
                  <td>{r.draws}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </section>
      )}

      {profile.published_bots.length > 0 && (
        <section>
          <h2>Published bots</h2>
          <ul className="bot-list">
            {profile.published_bots.map((bot) => (
              <li key={bot.id} className="bot-item">
                <span className="bot-select-btn">
                  <strong>{bot.name}</strong>
                  <span className="bot-meta">{bot.game_id} · v{bot.version}</span>
                </span>
                {isMe && <Link to={`/bots/${bot.id}/edit`} className="edit-link">Edit</Link>}
              </li>
            ))}
          </ul>
        </section>
      )}

      {matches.length > 0 && (
        <section>
          <h2>Recent matches</h2>
          <table className="leaderboard-table">
            <thead>
              <tr>
                <th>Match</th>
                <th>Game</th>
                <th>Status</th>
                <th>Result</th>
              </tr>
            </thead>
            <tbody>
              {matches.map((m) => (
                <tr key={m.id}>
                  <td>
                    <Link to={`/matches/${m.id}`}>#{m.id}</Link>
                  </td>
                  <td>{m.game_id}</td>
                  <td>{m.status}</td>
                  <td>
                    {m.status === "completed"
                      ? m.winner_index === null
                        ? "Draw"
                        : `P${m.winner_index + 1} wins`
                      : "—"}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </section>
      )}

      {profile.ratings.length === 0 && profile.published_bots.length === 0 && matches.length === 0 && (
        <p className="muted">No activity yet.</p>
      )}
    </main>
  );
}
