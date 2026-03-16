import { Link } from "react-router-dom";

export function Home() {
  return (
    <main>
      <h1>BotArena</h1>
      <p>Write bots. Challenge players. Climb the leaderboard.</p>
      <nav>
        <Link to="/games">Browse games</Link>
      </nav>
    </main>
  );
}
