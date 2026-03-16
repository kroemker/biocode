import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "@/api/client";
import type { GameInfo } from "@/types";

export function Games() {
  const [games, setGames] = useState<GameInfo[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api.get<GameInfo[]>("/games/").then(setGames).catch((e) => setError(e.message));
  }, []);

  if (error) return <p>Error: {error}</p>;

  return (
    <main>
      <h1>Games</h1>
      {games.length === 0 && <p>No games available yet.</p>}
      <ul>
        {games.map((g) => (
          <li key={g.game_id}>
            <Link to={`/games/${g.game_id}`}>
              <strong>{g.name}</strong>
            </Link>{" "}
            — {g.description}
          </li>
        ))}
      </ul>
    </main>
  );
}
