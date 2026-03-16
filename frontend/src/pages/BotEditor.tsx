import { useEffect, useState } from "react";
import { useNavigate, useParams, useSearchParams } from "react-router-dom";
import { bots as botsApi } from "@/api/client";
import { CodeEditor } from "@/components/Editor/CodeEditor";

const PLACEHOLDER = `# Write your Rulix bot here.
# Available variables each turn:
#   my_x, my_y, my_health
#   enemy_x, enemy_y, enemy_health
#   turn, grid_size
#
# Set the \`action\` variable to one of:
#   "move_n" | "move_s" | "move_e" | "move_w" | "attack" | "wait"

=> action = "wait"

# Close horizontal gap
enemy_x > my_x => action = "move_e"
enemy_x < my_x => action = "move_w"

# Attack when adjacent
abs(enemy_x - my_x) <= 1, abs(enemy_y - my_y) <= 1 => action = "attack"
`;

export function BotEditor() {
  const { botId } = useParams<{ botId?: string }>();
  const [searchParams] = useSearchParams();
  const gameId = searchParams.get("game") ?? "rulixbots_v1";
  const navigate = useNavigate();

  const isNew = botId === undefined;
  const [name, setName] = useState("My Bot");
  const [code, setCode] = useState(PLACEHOLDER);
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  const [publishing, setPublishing] = useState(false);
  const [isPublished, setIsPublished] = useState(false);
  const [currentBotId, setCurrentBotId] = useState<number | null>(null);

  useEffect(() => {
    if (!isNew && botId) {
      botsApi
        .get(Number(botId))
        .then((bot) => {
          setName(bot.name);
          setCode(bot.code);
          setIsPublished(bot.is_published);
          setCurrentBotId(bot.id);
        })
        .catch((e) => setError(e.message));
    }
  }, [botId, isNew]);

  async function handleSave() {
    setError(null);
    setSaving(true);
    setSaved(false);
    try {
      if (isNew) {
        const bot = await botsApi.create(gameId, name, code);
        setCurrentBotId(bot.id);
        navigate(`/bots/${bot.id}/edit`, { replace: true });
      } else {
        await botsApi.update(Number(botId), { name, code });
      }
      setSaved(true);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setSaving(false);
    }
  }

  async function handlePublish() {
    const id = currentBotId ?? Number(botId);
    if (!id) return;
    setError(null);
    setPublishing(true);
    try {
      await botsApi.publish(id);
      setIsPublished(true);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setPublishing(false);
    }
  }

  return (
    <div className="bot-editor">
      <header className="bot-editor-header">
        <input
          className="bot-name-input"
          value={name}
          onChange={(e) => setName(e.target.value)}
          placeholder="Bot name"
        />
        <div className="bot-editor-actions">
          {error && <span className="error">{error}</span>}
          {saved && <span className="success">Saved</span>}
          {isPublished && <span className="badge">Published</span>}
          <button onClick={handleSave} disabled={saving}>
            {saving ? "Saving…" : "Save"}
          </button>
          <button onClick={handlePublish} disabled={publishing || isPublished} title="Published bots can be challenged by other players">
            {isPublished ? "Published" : publishing ? "Publishing…" : "Publish"}
          </button>
          <button onClick={() => navigate(`/games/${gameId}`)}>← Back to lobby</button>
        </div>
      </header>
      <div className="editor-pane">
        <CodeEditor value={code} onChange={setCode} language="plaintext" />
      </div>
    </div>
  );
}
