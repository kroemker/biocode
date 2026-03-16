import { BrowserRouter, Link, Navigate, Route, Routes } from "react-router-dom";
import { AuthProvider, useAuth } from "@/context/AuthContext";
import { BotEditor } from "@/pages/BotEditor";
import { BrowseBots } from "@/pages/BrowseBots";
import { GameLobby } from "@/pages/GameLobby";
import { Games } from "@/pages/Games";
import { Home } from "@/pages/Home";
import { Leaderboard } from "@/pages/Leaderboard";
import { Login } from "@/pages/Login";
import { MatchViewer } from "@/pages/MatchViewer";
import { MyMatches } from "@/pages/MyMatches";
import { NotFound } from "@/pages/NotFound";
import { Profile } from "@/pages/Profile";
import { Register } from "@/pages/Register";

function Nav() {
  const { user, logout } = useAuth();
  return (
    <nav className="top-nav">
      <Link to="/" className="nav-brand">BotArena</Link>
      <div className="nav-links">
        <Link to="/games">Games</Link>
        {user ? (
          <>
            <Link to="/my/matches">My matches</Link>
            <Link to={`/players/${user.username}`}>{user.username}</Link>
            <button className="nav-logout" onClick={logout}>Sign out</button>
          </>
        ) : (
          <>
            <Link to="/login">Sign in</Link>
            <Link to="/register">Register</Link>
          </>
        )}
      </div>
    </nav>
  );
}

function RequireAuth({ children }: { children: React.ReactNode }) {
  const { user, loading } = useAuth();
  if (loading) return null;
  if (!user) return <Navigate to="/login" replace />;
  return <>{children}</>;
}

function AppRoutes() {
  return (
    <>
      <Nav />
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />
        <Route path="/games" element={<Games />} />
        <Route path="/games/:gameId" element={<GameLobby />} />
        <Route path="/leaderboard/:gameId" element={<Leaderboard />} />
        <Route path="/games/:gameId/bots" element={<BrowseBots />} />
        <Route path="/players/:username" element={<Profile />} />
        <Route
          path="/my/matches"
          element={<RequireAuth><MyMatches /></RequireAuth>}
        />
        <Route
          path="/bots/new/edit"
          element={<RequireAuth><BotEditor /></RequireAuth>}
        />
        <Route
          path="/bots/:botId/edit"
          element={<RequireAuth><BotEditor /></RequireAuth>}
        />
        <Route path="/matches/:matchId" element={<MatchViewer />} />
        <Route path="*" element={<NotFound />} />
      </Routes>
    </>
  );
}

export function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <AppRoutes />
      </AuthProvider>
    </BrowserRouter>
  );
}
