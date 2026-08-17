import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../../api/client";

interface World {
  id: string;
  name: string;
  description?: string | null;
  tags: string[];
  locations?: unknown[];
  factions?: unknown[];
}

export default function WorldBrowser() {
  const [worlds, setWorlds] = useState<World[]>([]);
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [tags, setTags] = useState("");
  const [busy, setBusy] = useState(false);
  const [showForm, setShowForm] = useState(false);

  async function load() {
    const list = await api.get<World[]>("/worlds");
    setWorlds(list);
  }

  useEffect(() => {
    load().catch(console.error);
  }, []);

  async function create() {
    if (!name.trim()) return;
    setBusy(true);
    try {
      await api.post("/worlds", {
        name: name.trim(),
        description: description.trim(),
        tags: tags
          .split(",")
          .map((t) => t.trim())
          .filter(Boolean),
      });
      setName("");
      setDescription("");
      setTags("");
      setShowForm(false);
      await load();
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">Worlds</h1>
          <p className="text-sm text-slate-400 mt-1">
            Shared settings, rules, locations, and factions bound to chats.
          </p>
        </div>
        <button
          type="button"
          className="btn btn-primary text-sm"
          onClick={() => setShowForm((v) => !v)}
        >
          {showForm ? "Close" : "+ New world"}
        </button>
      </div>

      {showForm && (
        <section className="card p-5 space-y-3 max-w-xl">
          <h2 className="font-medium">Create world</h2>
          <input
            className="w-full bg-surface-950 border border-slate-700 rounded-lg px-3 py-2 text-sm"
            placeholder="Name — e.g. Eldoria"
            value={name}
            onChange={(e) => setName(e.target.value)}
          />
          <textarea
            className="w-full bg-surface-950 border border-slate-700 rounded-lg px-3 py-2 text-sm min-h-[80px]"
            placeholder="Short description"
            value={description}
            onChange={(e) => setDescription(e.target.value)}
          />
          <input
            className="w-full bg-surface-950 border border-slate-700 rounded-lg px-3 py-2 text-sm"
            placeholder="Tags — fantasy, coastal, war"
            value={tags}
            onChange={(e) => setTags(e.target.value)}
          />
          <button
            type="button"
            disabled={busy || !name.trim()}
            onClick={create}
            className="btn btn-primary"
          >
            Create
          </button>
        </section>
      )}

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        {worlds.map((w) => (
          <div key={w.id} className="card p-4 hover:border-accent/40 transition group">
            <Link to={`/worlds/${w.id}`} className="block">
              <h3 className="font-medium">{w.name}</h3>
              <p className="text-sm text-slate-400 mt-1 line-clamp-3">
                {w.description || "No description"}
              </p>
              <div className="flex flex-wrap gap-1 mt-2">
                {(w.tags || []).slice(0, 4).map((t) => (
                  <span
                    key={t}
                    className="text-[10px] px-1.5 py-0.5 rounded bg-surface-800 text-slate-400"
                  >
                    {t}
                  </span>
                ))}
              </div>
              <p className="text-[11px] text-slate-500 mt-2">
                {(w.locations as unknown[] | undefined)?.length || 0} locations ·{" "}
                {(w.factions as unknown[] | undefined)?.length || 0} factions
              </p>
            </Link>
            <div className="mt-3 flex gap-2">
              <Link
                to={`/worlds/${w.id}`}
                className="text-xs px-2.5 py-1 rounded-md bg-surface-800 text-slate-300"
              >
                Edit
              </Link>
              <button
                type="button"
                className="text-xs px-2.5 py-1 rounded-md text-red-400/80 hover:bg-red-950/40"
                onClick={async () => {
                  if (!confirm(`Delete world "${w.name}"?`)) return;
                  await api.delete(`/worlds/${w.id}`);
                  await load();
                }}
              >
                Delete
              </button>
            </div>
          </div>
        ))}
      </div>

      {worlds.length === 0 && (
        <p className="text-slate-500 text-sm">No worlds yet. Create one to attach to chats.</p>
      )}
    </div>
  );
}
