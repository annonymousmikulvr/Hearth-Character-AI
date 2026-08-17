import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { conversationsApi } from "../../api/conversations";
import type { ConversationListItem } from "../../types";

export default function ConversationList() {
  const [items, setItems] = useState<ConversationListItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    conversationsApi
      .list()
      .then(setItems)
      .catch((e) => setError(String(e)))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-semibold">Chats</h1>
          <p className="text-sm text-slate-400 mt-1">
            All conversations are stored locally in your database.
          </p>
        </div>
        <Link
          to="/chats/new"
          className="px-4 py-2 rounded-md bg-accent hover:bg-accent-hover text-sm font-medium"
        >
          New Chat
        </Link>
      </div>

      {loading && <p className="text-slate-400 text-sm">Loading…</p>}
      {error && (
        <p className="text-sm text-red-400 bg-red-950/40 border border-red-900 rounded-md px-3 py-2">
          {error}
        </p>
      )}

      <div className="space-y-2">
        {items.map((c) => (
          <div
            key={c.id}
            className="flex items-center gap-4 bg-surface-900 border border-slate-800 rounded-xl px-4 py-3 hover:border-accent/50 transition group"
          >
          <Link
            to={`/chats/${c.id}`}
            className="flex items-center gap-4 flex-1 min-w-0"
          >
            <div className="w-10 h-10 rounded-full bg-surface-800 flex items-center justify-center text-sm font-semibold text-accent-muted shrink-0">
              {(c.character_name || "?").charAt(0).toUpperCase()}
            </div>
            <div className="min-w-0 flex-1">
              <div className="font-medium truncate">
                {c.title || `Chat with ${c.character_name || "Unknown"}`}
              </div>
              <div className="text-xs text-slate-400 truncate">
                {c.character_name}
                {" · "}
                as {c.persona_display_name}
                {c.last_message_at && (
                  <>
                    {" · "}
                    {new Date(c.last_message_at + "Z").toLocaleString()}
                  </>
                )}
              </div>
            </div>
          </Link>
          <button
            type="button"
            className="text-xs text-slate-500 hover:text-red-400 opacity-0 group-hover:opacity-100 px-2"
            onClick={async (e) => {
              e.preventDefault();
              if (!confirm("Permanently delete this chat?")) return;
              await conversationsApi.remove(c.id, true);
              setItems((prev) => prev.filter((x) => x.id !== c.id));
            }}
          >
            Delete
          </button>
          </div>
        ))}
      </div>

      {!loading && items.length === 0 && (
        <p className="text-slate-500 text-sm mt-8">
          No chats yet. Start one with a character and persona.
        </p>
      )}
    </div>
  );
}
