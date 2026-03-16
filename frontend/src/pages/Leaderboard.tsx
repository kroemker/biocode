import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { leaderboard as leaderboardApi } from "@/api/client";
import type { LeaderboardEntry } from "@/types";

export function Leaderboard() {
  const { gameId } = useParams<{ gameId: string }>();
  const [entries, setEntries] = useState<LeaderboardEntry[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!gameId) return;
    leaderboardApi
      .get(gameId)
      .then(setEntries)
      .catch((e) => setError(e.message));
  }, [gameId]);

  return (
    <main className="leaderboard">
      <nav className="breadcrumb">
        <Link to="/games">Games</Link> / <Link to={`/games/${gameId}`}>{gameId}</Link> / Leaderboard
      </nav>
      <h1>Leaderboard</h1>
      {error && <p className="error">{error}</p>}
      {entries.length === 0 && !error && <p>No ranked players yet.</p>}
      {entries.length > 0 && (
        <table className="leaderboard-table">
          <thead>
            <tr>
              <th>#</th>
              <th>Player</th>
              <th>Elo</th>
              <th>W</th>
              <th>L</th>
              <th>D</th>
            </tr>
          </thead>
          <tbody>
            {entries.map((e) => (
              <tr key={e.user_id}>
                <td>{e.rank}</td>
                <td>{e.username}</td>
                <td><strong>{e.elo}</strong></td>
                <td className="win">{e.wins}</td>
                <td className="loss">{e.losses}</td>
                <td>{e.draws}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </main>
  );
}
