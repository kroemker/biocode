/**
 * Typed API client. All requests go through /api (proxied to the backend).
 * Token is stored in localStorage so it survives page refreshes.
 */
import type { Bot, BotWithCode, GameInfo, LeaderboardEntry, Match, MatchReplay, PublicBot, SampleBot, User, UserProfile } from "@/types";

const TOKEN_KEY = "botarena_token";

export function getToken(): string | null {
  return localStorage.getItem(TOKEN_KEY);
}
export function setToken(token: string) {
  localStorage.setItem(TOKEN_KEY, token);
}
export function clearToken() {
  localStorage.removeItem(TOKEN_KEY);
}

async function request<T>(method: string, path: string, body?: unknown): Promise<T> {
  const headers: Record<string, string> = {};
  const token = getToken();
  if (token) headers["Authorization"] = `Bearer ${token}`;
  if (body !== undefined) headers["Content-Type"] = "application/json";

  const res = await fetch(`/api${path}`, {
    method,
    headers,
    body: body !== undefined ? JSON.stringify(body) : undefined,
  });

  if (!res.ok) {
    const detail = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(detail.detail ?? res.statusText);
  }
  return res.json() as Promise<T>;
}

async function formPost<T>(path: string, data: Record<string, string>): Promise<T> {
  const res = await fetch(`/api${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body: new URLSearchParams(data).toString(),
  });
  if (!res.ok) {
    const detail = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(detail.detail ?? res.statusText);
  }
  return res.json() as Promise<T>;
}

export const auth = {
  register: (username: string, email: string, password: string) =>
    request<User>("POST", "/auth/register", { username, email, password }),
  login: (username: string, password: string) =>
    formPost<{ access_token: string; token_type: string }>("/auth/token", { username, password }),
  me: () => request<User>("GET", "/auth/me"),
};

export const games = {
  list: () => request<GameInfo[]>("GET", "/games/"),
  get: (gameId: string) => request<GameInfo>("GET", `/games/${gameId}`),
  sampleBots: (gameId: string) => request<SampleBot[]>("GET", `/games/${gameId}/sample-bots`),
  publishedBots: (gameId: string) => request<PublicBot[]>("GET", `/games/${gameId}/bots`),
};

export const users = {
  profile: (username: string) => request<UserProfile>("GET", `/users/${username}`),
  matches: (username: string) => request<Match[]>("GET", `/users/${username}/matches`),
};

export const bots = {
  list: () => request<Bot[]>("GET", "/bots/"),
  get: (botId: number) => request<BotWithCode>("GET", `/bots/${botId}`),
  create: (gameId: string, name: string, code: string) =>
    request<Bot>("POST", "/bots/", { game_id: gameId, name, code }),
  update: (botId: number, data: { name?: string; code?: string }) =>
    request<Bot>("PATCH", `/bots/${botId}`, data),
  publish: (botId: number) => request<Bot>("POST", `/bots/${botId}/publish`),
};

export const matches = {
  request: (gameId: string, botId: number, opponentBotId: number) =>
    request<Match>("POST", "/matches/", { game_id: gameId, bot_id: botId, opponent_bot_id: opponentBotId }),
  test: (gameId: string, botId: number, sampleBotName: string) =>
    request<Match>("POST", "/matches/test", { game_id: gameId, bot_id: botId, sample_bot_name: sampleBotName }),
  get: (matchId: number) => request<MatchReplay>("GET", `/matches/${matchId}`),
  my: () => request<Match[]>("GET", "/matches/my"),
};

export const leaderboard = {
  get: (gameId: string) => request<LeaderboardEntry[]>("GET", `/leaderboard/${gameId}`),
};
