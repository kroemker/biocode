/**
 * RulixBots canvas renderer.
 *
 * Receives a state snapshot (matching the server-side game state dict) and
 * draws the current turn onto a 2D canvas context.
 *
 * State shape:
 *   { turn: number, grid_size: number, bots: [{x,y,health}, {x,y,health}] }
 */

interface BotState {
  x: number;
  y: number;
  health: number;
}

interface RulixBotsSnapshot {
  turn: number;
  grid_size: number;
  bots: BotState[];
}

const PLAYER_COLORS = ["#4f8ef7", "#f7604f"]; // blue, red
const PLAYER_LABELS = ["P1", "P2"];
const MAX_HEALTH = 100;

export function renderRulixBots(ctx: CanvasRenderingContext2D, snapshot: unknown): void {
  const state = snapshot as RulixBotsSnapshot;
  const { grid_size, bots, turn } = state;

  const W = ctx.canvas.width;
  const H = ctx.canvas.height;
  const padding = 40;
  const boardSize = Math.min(W - padding * 2, H - padding - 80);
  const cellSize = boardSize / grid_size;
  const originX = (W - boardSize) / 2;
  const originY = padding + 40; // leave room for health bars at top

  // Background
  ctx.fillStyle = "#1a1a2e";
  ctx.fillRect(0, 0, W, H);

  // Grid
  ctx.strokeStyle = "#2a2a4a";
  ctx.lineWidth = 1;
  for (let i = 0; i <= grid_size; i++) {
    const x = originX + i * cellSize;
    const y = originY + i * cellSize;
    ctx.beginPath();
    ctx.moveTo(x, originY);
    ctx.lineTo(x, originY + boardSize);
    ctx.stroke();
    ctx.beginPath();
    ctx.moveTo(originX, y);
    ctx.lineTo(originX + boardSize, y);
    ctx.stroke();
  }

  // Health bars at top
  bots.forEach((bot, i) => {
    const barW = 160;
    const barH = 14;
    const barX = i === 0 ? 20 : W - 20 - barW;
    const barY = 14;

    // Label
    ctx.fillStyle = PLAYER_COLORS[i];
    ctx.font = "bold 13px monospace";
    ctx.textAlign = i === 0 ? "left" : "right";
    ctx.fillText(PLAYER_LABELS[i], i === 0 ? barX : barX + barW, barY - 2);

    // Bar background
    ctx.fillStyle = "#333";
    ctx.fillRect(barX, barY, barW, barH);

    // Bar fill
    const pct = Math.max(0, bot.health / MAX_HEALTH);
    const hue = pct > 0.5 ? 120 : pct > 0.25 ? 60 : 0;
    ctx.fillStyle = `hsl(${hue}, 70%, 50%)`;
    ctx.fillRect(barX, barY, barW * pct, barH);

    // HP text
    ctx.fillStyle = "#fff";
    ctx.font = "11px monospace";
    ctx.textAlign = "center";
    ctx.fillText(`${bot.health} HP`, barX + barW / 2, barY + barH - 2);
  });

  // Turn counter
  ctx.fillStyle = "#888";
  ctx.font = "12px monospace";
  ctx.textAlign = "center";
  ctx.fillText(`Turn ${turn}`, W / 2, 22);

  // Bots
  bots.forEach((bot, i) => {
    if (bot.health <= 0) return;

    const cx = originX + bot.x * cellSize + cellSize / 2;
    const cy = originY + bot.y * cellSize + cellSize / 2;
    const radius = cellSize * 0.38;

    // Glow
    ctx.shadowColor = PLAYER_COLORS[i];
    ctx.shadowBlur = 12;
    ctx.fillStyle = PLAYER_COLORS[i];
    ctx.beginPath();
    ctx.arc(cx, cy, radius, 0, Math.PI * 2);
    ctx.fill();
    ctx.shadowBlur = 0;

    // Label
    ctx.fillStyle = "#fff";
    ctx.font = `bold ${Math.max(10, cellSize * 0.35)}px monospace`;
    ctx.textAlign = "center";
    ctx.textBaseline = "middle";
    ctx.fillText(PLAYER_LABELS[i], cx, cy);
    ctx.textBaseline = "alphabetic";
  });

  // Dead bots — show a faded ✕
  bots.forEach((bot, i) => {
    if (bot.health > 0) return;
    const cx = originX + bot.x * cellSize + cellSize / 2;
    const cy = originY + bot.y * cellSize + cellSize / 2;
    ctx.fillStyle = `${PLAYER_COLORS[i]}55`;
    ctx.font = `bold ${Math.max(10, cellSize * 0.4)}px monospace`;
    ctx.textAlign = "center";
    ctx.textBaseline = "middle";
    ctx.fillText("✕", cx, cy);
    ctx.textBaseline = "alphabetic";
  });
}
