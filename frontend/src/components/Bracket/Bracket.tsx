import { Link } from "react-router-dom";
import type { TournamentMatch } from "@/types";

interface BracketProps {
  bracket: TournamentMatch[];
  totalRounds: number;
}

/**
 * Single-elimination bracket viewer.
 *
 * Layout: one flex column per round, left → right.
 * Matches in each round are spaced evenly with justify-content: space-around.
 * The vertical space doubles every round, naturally centering each match
 * between the two feeders from the previous round.
 */
export function Bracket({ bracket, totalRounds }: BracketProps) {
  // Group matches by round
  const rounds: TournamentMatch[][] = [];
  for (let r = 1; r <= totalRounds; r++) {
    rounds.push(
      bracket
        .filter((m) => m.round === r)
        .sort((a, b) => a.position - b.position)
    );
  }

  const roundLabels: Record<number, string> = {};
  if (totalRounds >= 1) roundLabels[totalRounds] = "Final";
  if (totalRounds >= 2) roundLabels[totalRounds - 1] = "Semi-final";
  if (totalRounds >= 3) roundLabels[totalRounds - 2] = "Quarter-final";

  return (
    <div className="bracket">
      {rounds.map((matches, idx) => {
        const roundNum = idx + 1;
        const label = roundLabels[roundNum] ?? `Round ${roundNum}`;
        return (
          <div key={roundNum} className="bracket-round">
            <div className="bracket-round-label">{label}</div>
            <div className="bracket-matches">
              {matches.map((m) => (
                <BracketMatchCard key={m.id} match={m} />
              ))}
            </div>
          </div>
        );
      })}
    </div>
  );
}

function BracketMatchCard({ match }: { match: TournamentMatch }) {
  const bot1Won = match.winner_bot_id === match.bot1_id && match.bot1_id !== null;
  const bot2Won = match.winner_bot_id === match.bot2_id && match.bot2_id !== null;

  return (
    <div className={`bracket-match ${match.is_bye ? "bye" : ""}`}>
      <BracketSlot
        name={match.bot1_name}
        won={bot1Won}
        pending={!match.bot1_id}
      />
      {!match.is_bye && (
        <BracketSlot
          name={match.bot2_name}
          won={bot2Won}
          pending={!match.bot2_id}
        />
      )}
      {match.is_bye && (
        <div className="bracket-slot bye-label">bye</div>
      )}
      {match.match_id && !match.is_bye && (
        <Link to={`/matches/${match.match_id}`} className="match-link">
          View replay
        </Link>
      )}
    </div>
  );
}

function BracketSlot({
  name,
  won,
  pending,
}: {
  name: string | null;
  won: boolean;
  pending: boolean;
}) {
  return (
    <div
      className={[
        "bracket-slot",
        won ? "winner" : "",
        pending ? "tbd" : "",
      ]
        .filter(Boolean)
        .join(" ")}
    >
      {name ?? (pending ? "TBD" : "—")}
    </div>
  );
}
