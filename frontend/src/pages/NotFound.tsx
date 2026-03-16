import { Link } from "react-router-dom";

export function NotFound() {
  return (
    <main>
      <h1>404 — Page not found</h1>
      <Link to="/">Go home</Link>
    </main>
  );
}
