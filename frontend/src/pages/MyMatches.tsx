import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { matches as matchesApi } from "@/api/client";
import type { Match } from "@/types";

export function MyMatches() {
  const [matchList, setMatchList] = useState<Match[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    matchesApi
      .my()
      .then(setMatchList)
      .catch((e) => setError(e.message));
  }, []);

  return (
    <main>
      <h1>My matches</h1>
      {error && <p className="error">{error}</p>}
      {matchList.length === 0 && !error && <p>No matches yet.</p>}
      {matchList.length > 0 && (
        <table className="leaderboard-table">
          <thead>
            <tr>
              <th>Match</th>
              <th>Game</th>
              <th>Status</th>
              <th>Result</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {matchList.map((m) => (
              <tr key={m.id}>
                <td>#{m.id}</td>
                <td>{m.game_id}</td>
                <td>{m.status}</td>
                <td>
                  {m.status === "completed"
                    ? m.winner_index === null
                      ? "Draw"
                      : `P${m.winner_index + 1} wins`
                    : "—"}
                </td>
                <td><Link to={`/matches/${m.id}`}>View</Link></td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </main>
  );
}
