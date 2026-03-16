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

export interface PublicBot {
  id: number;
  owner_id: number;
  owner_username: string;
  game_id: string;
  name: string;
  version: number;
}

export interface RatingSummary {
  game_id: string;
  elo: number;
  wins: number;
  losses: number;
  draws: number;
}

export interface UserProfile {
  id: number;
  username: string;
  ratings: RatingSummary[];
  published_bots: PublicBot[];
}

export interface TournamentOut {
  id: number;
  name: string;
  game_id: string;
  status: "registration" | "active" | "completed";
  max_participants: number;
  created_by: number;
  participant_count: number;
  winner_bot_id: number | null;
  winner_bot_name: string | null;
}

export interface TournamentMatch {
  id: number;
  round: number;
  position: number;
  bot1_id: number | null;
  bot1_name: string | null;
  bot2_id: number | null;
  bot2_name: string | null;
  match_id: number | null;
  winner_bot_id: number | null;
  is_bye: boolean;
}

export interface TournamentDetail extends TournamentOut {
  total_rounds: number;
  bracket: TournamentMatch[];
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
