import { Link } from "react-router-dom";
import { useAuth } from "@/context/AuthContext";

export function Home() {
  const { user } = useAuth();
  return (
    <main className="home">
      <h1>BotArena</h1>
      <p className="tagline">Write bots. Challenge players. Climb the leaderboard.</p>
      <div className="home-actions">
        <Link to="/games" className="button-link primary">Browse games</Link>
        {!user && <Link to="/register" className="button-link">Create account</Link>}
      </div>
    </main>
  );
}
