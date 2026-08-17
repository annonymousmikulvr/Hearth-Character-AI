import { useEffect, useState } from "react";
import { api } from "../../api/client";

interface Memory {
  id: string;
  owner_type: string;
  owner_id: string;
  content: string;
  category?: string | null;
  importance: number;
  confidence: number;
  created_at?: string | null;
}

export default function MemoryBrowser() {
  const [items, setItems] = useState<Memory[]>([]);
  const [content, setContent] = useState("");
  const [ownerType, setOwnerType] = useState("global");

  async function load() {
    setItems(await api.get<Memory[]>("/memories?limit=200"));
  }

  useEffect(() => {
    load().catch(console.error);
  }, []);

  async function add() {
    if (!content.trim()) return;
    await api.post("/memories", {
      owner_type: ownerType,
      owner_id: ownerType === "global" ? "global" : ownerType,
      content: content.trim(),
      category: "fact",
      importance: 0.7,
    });
    setContent("");
    await load();
  }

  async function remove(id: string) {
    await api.delete(`/memories/${id}`);
    await load();
  }

  return (
    <div className="space-y-6 max-w-3xl">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">Memory Graph</h1>
        <p className="text-sm text-slate-400 mt-1">
          Facts the AI can recall across chats. Auto-extracted from your messages and manually editable.
        </p>
      </div>

      <section className="card p-5 space-y-3">
        <div className="flex gap-2 flex-wrap">
          <select
            className="bg-surface-950 border border-slate-700 rounded-lg px-3 py-2 text-sm"
            value={ownerType}
            onChange={(e) => setOwnerType(e.target.value)}
          >
            <option value="global">Global</option>
            <option value="persona">Persona-scoped</option>
            <option value="character">Character-scoped</option>
          </select>
          <input
            className="flex-1 min-w-[200px] bg-surface-950 border border-slate-700 rounded-lg px-3 py-2 text-sm"
            placeholder="Add a memory fact…"
            value={content}
            onChange={(e) => setContent(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && add()}
          />
          <button type="button" className="btn btn-primary" onClick={add}>
            Add
          </button>
        </div>
      </section>

      <div className="space-y-2">
        {items.map((m) => (
          <div
            key={m.id}
            className="card px-4 py-3 flex items-start gap-3 justify-between"
          >
            <div className="min-w-0">
              <div className="text-sm">{m.content}</div>
              <div className="text-[11px] text-slate-500 mt-1">
                {m.owner_type}
                {m.category ? ` · ${m.category}` : ""}
                {` · importance ${m.importance.toFixed(2)}`}
              </div>
            </div>
            <button
              type="button"
              className="text-xs text-slate-500 hover:text-amber-400"
              onClick={async () => {
                await api.post(`/advanced/memories/${m.id}/pin?pinned=true`, {});
                await load();
              }}
            >
              Pin
            </button>
            <button
              type="button"
              className="text-xs text-slate-500 hover:text-red-400"
              onClick={() => remove(m.id)}
            >
              Remove
            </button>
          </div>
        ))}
        {items.length === 0 && (
          <p className="text-slate-500 text-sm">No memories yet. Chat or add one above.</p>
        )}
      </div>
    </div>
  );
}
