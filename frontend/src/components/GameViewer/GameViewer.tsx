import { useEffect, useRef } from "react";

interface Props {
  /** All state snapshots for the match, one entry per turn. */
  snapshots: unknown[];
  /** Index of the snapshot currently displayed. */
  currentTurn: number;
  /**
   * Game-specific render function. Receives the canvas context and the
   * state snapshot for the current turn. Provided by each game's renderer.
   */
  render: (ctx: CanvasRenderingContext2D, snapshot: unknown) => void;
  width?: number;
  height?: number;
}

/**
 * Generic match viewer. Games supply their own `render` function; this
 * component handles the canvas lifecycle and re-draws whenever the turn
 * or snapshot changes.
 */
export function GameViewer({ snapshots, currentTurn, render, width = 600, height = 600 }: Props) {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    const snapshot = snapshots[currentTurn];
    if (snapshot === undefined) return;

    ctx.clearRect(0, 0, width, height);
    render(ctx, snapshot);
  }, [snapshots, currentTurn, render, width, height]);

  return <canvas ref={canvasRef} width={width} height={height} />;
}
