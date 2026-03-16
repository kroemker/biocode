import { useCallback, useEffect, useRef, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { matches as matchesApi } from "@/api/client";
import { GameViewer } from "@/components/GameViewer/GameViewer";
import { renderRulixBots } from "@/games/rulixbots/renderer";
import type { MatchReplay } from "@/types";

const RENDERERS: Record<string, (ctx: CanvasRenderingContext2D, snapshot: unknown) => void> = {
  rulixbots_v1: renderRulixBots,
};

const POLL_INTERVAL_MS = 1000;
const PLAYBACK_INTERVAL_MS = 300;

export function MatchViewer() {
  const { matchId } = useParams<{ matchId: string }>();
  const [match, setMatch] = useState<MatchReplay | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [currentTurn, setCurrentTurn] = useState(0);
  const [playing, setPlaying] = useState(false);
  const playIntervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  // Poll until match completes
  useEffect(() => {
    if (!matchId) return;
    let cancelled = false;

    async function poll() {
      try {
        const data = await matchesApi.get(Number(matchId));
        if (cancelled) return;
        setMatch(data);
        if (data.status === "completed" || data.status === "error") return;
        setTimeout(poll, POLL_INTERVAL_MS);
      } catch (e) {
        if (!cancelled) setError((e as Error).message);
      }
    }

    poll();
    return () => { cancelled = true; };
  }, [matchId]);

  // Playback
  useEffect(() => {
    if (playing && match?.replay) {
      playIntervalRef.current = setInterval(() => {
        setCurrentTurn((t) => {
          if (t >= (match.replay?.length ?? 1) - 1) {
            setPlaying(false);
            return t;
          }
          return t + 1;
        });
      }, PLAYBACK_INTERVAL_MS);
    }
    return () => {
      if (playIntervalRef.current) clearInterval(playIntervalRef.current);
    };
  }, [playing, match]);

  const handlePlay = useCallback(() => {
    if (currentTurn >= (match?.replay?.length ?? 1) - 1) {
      setCurrentTurn(0);
    }
    setPlaying(true);
  }, [currentTurn, match]);

  const renderFn = match ? RENDERERS[match.game_id] : undefined;
  const snapshots = match?.replay ?? [];
  const totalTurns = snapshots.length;
  const isPending = !match || match.status === "pending" || match.status === "running";

  function resultText(): string {
    if (!match || match.status !== "completed") return "";
    if (match.winner_index === null) return "Draw";
    return `Player ${match.winner_index + 1} wins`;
  }

  return (
    <main className="match-viewer">
      <nav className="breadcrumb">
        <Link to="/games">Games</Link> / Match #{matchId}
      </nav>

      {error && <p className="error">{error}</p>}

      {isPending && (
        <div className="match-pending">
          <p>⏳ Match is {match?.status ?? "loading"}…</p>
          <p className="hint">This page updates automatically.</p>
        </div>
      )}

      {match?.status === "completed" && (
        <>
          <div className="match-result">{resultText()}</div>

          <div className="viewer-canvas">
            {renderFn ? (
              <GameViewer
                snapshots={snapshots}
                currentTurn={currentTurn}
                render={renderFn}
                width={520}
                height={560}
              />
            ) : (
              <p>No renderer available for game <code>{match.game_id}</code>.</p>
            )}
          </div>

          <div className="replay-controls">
            <button onClick={() => { setPlaying(false); setCurrentTurn(0); }}>⏮</button>
            <button onClick={() => { setPlaying(false); setCurrentTurn((t) => Math.max(0, t - 1)); }}>◀</button>
            {playing ? (
              <button onClick={() => setPlaying(false)}>⏸</button>
            ) : (
              <button onClick={handlePlay}>▶</button>
            )}
            <button onClick={() => { setPlaying(false); setCurrentTurn((t) => Math.min(totalTurns - 1, t + 1)); }}>▶</button>
            <button onClick={() => { setPlaying(false); setCurrentTurn(totalTurns - 1); }}>⏭</button>
            <span className="turn-counter">Turn {currentTurn} / {Math.max(0, totalTurns - 1)}</span>
          </div>
        </>
      )}

      {match?.status === "error" && <p className="error">Match encountered an error.</p>}
    </main>
  );
}
