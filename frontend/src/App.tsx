import { BrowserRouter, Route, Routes } from "react-router-dom";
import { Games } from "@/pages/Games";
import { Home } from "@/pages/Home";
import { NotFound } from "@/pages/NotFound";

export function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/games" element={<Games />} />
        <Route path="*" element={<NotFound />} />
      </Routes>
    </BrowserRouter>
  );
}
