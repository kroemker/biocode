export interface User {
  id: number;
  username: string;
  email: string;
}

export interface GameInfo {
  game_id: string;
  name: string;
  description: string;
  player_count: number;
  max_turns: number;
}

export interface SampleBot {
  name: string;
  description: string;
}

export interface Bot {
  id: number;
  owner_id: number;
  game_id: string;
  name: string;
  version: number;
  is_published: boolean;
}

export interface BotWithCode extends Bot {
  code: string;
}

export interface Match {
  id: number;
  game_id: string;
  status: "pending" | "running" | "completed" | "error";
  winner_index: number | null;
}

export interface MatchReplay extends Match {
  replay: unknown[] | null;
}

export interface LeaderboardEntry {
  rank: number;
  user_id: number;
  username: string;
  elo: number;
  wins: number;
  losses: number;
  draws: number;
}
