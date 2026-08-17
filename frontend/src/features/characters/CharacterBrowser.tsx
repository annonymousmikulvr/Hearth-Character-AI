import { useEffect, useState, useRef } from "react";
import { Link } from "react-router-dom";
import { useAppStore } from "../../stores/appStore";

export default function CharacterBrowser() {
  const { characters, loading, loadCharacters } = useAppStore();
  const [search, setSearch] = useState("");
  const fileRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    loadCharacters();
  }, []);

  useEffect(() => {
    const t = setTimeout(() => loadCharacters(search || undefined), 250);
    return () => clearTimeout(t);
  }, [search]);

  async function exportChar(id: string, name: string) {
    const res = await fetch(`/api/characters/${id}/export`);
    if (!res.ok) {
      alert("Export failed");
      return;
    }
    const blob = await res.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `${name.replace(/\s+/g, "_")}.char`;
    a.click();
    URL.revokeObjectURL(url);
  }

  async function importChar(file: File) {
    const fd = new FormData();
    fd.append("file", file);
    const res = await fetch("/api/characters/import", { method: "POST", body: fd });
    if (!res.ok) {
      alert(await res.text());
      return;
    }
    loadCharacters();
  }

  return (
    <div>
      <div className="flex flex-wrap items-center justify-between gap-3 mb-6">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">Characters</h1>
          <p className="text-sm text-slate-400 mt-0.5">
            AI personalities you chat with. Exportable as .char packages.
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <input
            ref={fileRef}
            type="file"
            accept=".char,.zip"
            className="hidden"
            onChange={(e) => {
              const f = e.target.files?.[0];
              if (f) importChar(f);
              e.target.value = "";
            }}
          />
          <button
            type="button"
            onClick={() => fileRef.current?.click()}
            className="px-3 py-2 rounded-lg bg-surface-800 hover:bg-surface-700 border border-slate-700 text-sm"
          >
            Import .char
          </button>
          <Link
            to="/characters/new"
            className="px-4 py-2 rounded-lg bg-accent hover:bg-accent-hover text-sm font-medium shadow-lg shadow-accent/20"
          >
            + New Character
          </Link>
        </div>
      </div>

      <input
        className="w-full max-w-md mb-6 bg-surface-900 border border-slate-700 rounded-lg px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-accent"
        placeholder="Search characters…"
        value={search}
        onChange={(e) => setSearch(e.target.value)}
      />

      {loading && <p className="text-slate-400 text-sm">Loading…</p>}

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        {characters.map((c) => (
          <div
            key={c.id}
            className="group bg-surface-900 border border-slate-800 rounded-2xl p-4 hover:border-accent/40 transition shadow-sm hover:shadow-accent/5"
          >
            <Link to={`/characters/${c.id}`} className="block">
              <div className="flex items-start gap-3">
                <div className="w-12 h-12 rounded-2xl bg-gradient-to-br from-accent/30 to-surface-800 flex items-center justify-center text-lg font-semibold text-accent-muted shrink-0 overflow-hidden">
                  {c.avatar_path ? (
                    <img src={c.avatar_path} alt="" className="w-full h-full object-cover" />
                  ) : (
                    c.name.charAt(0).toUpperCase()
                  )}
                </div>
                <div className="min-w-0">
                  <h3 className="font-medium truncate">{c.name}</h3>
                  <p className="text-sm text-slate-400 line-clamp-2 mt-0.5">
                    {c.description || "No description"}
                  </p>
                  {c.tags.length > 0 && (
                    <div className="flex flex-wrap gap-1 mt-2">
                      {c.tags.slice(0, 4).map((t) => (
                        <span
                          key={t}
                          className="text-[10px] px-1.5 py-0.5 rounded-md bg-surface-800 text-slate-400"
                        >
                          {t}
                        </span>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            </Link>
            <div className="mt-3 flex gap-2 opacity-80 group-hover:opacity-100">
              <Link
                to={`/chats/new?character=${c.id}`}
                className="text-xs px-2.5 py-1 rounded-md bg-accent/15 text-accent-muted hover:bg-accent/25"
              >
                Chat
              </Link>
              <button
                type="button"
                onClick={() => exportChar(c.id, c.name)}
                className="text-xs px-2.5 py-1 rounded-md bg-surface-800 text-slate-300 hover:bg-surface-700"
              >
                Export
              </button>
              <Link
                to={`/characters/${c.id}/edit`}
                className="text-xs px-2.5 py-1 rounded-md bg-surface-800 text-slate-300 hover:bg-surface-700"
              >
                Edit
              </Link>
              <button
                type="button"
                className="text-xs px-2.5 py-1 rounded-md bg-surface-800 text-red-400/80 hover:bg-red-950/40"
                onClick={async () => {
                  if (!confirm(`Delete character "${c.name}" permanently?`)) return;
                  await fetch(`/api/characters/${c.id}?hard=true`, { method: "DELETE" });
                  loadCharacters();
                }}
              >
                Delete
              </button>
            </div>
          </div>
        ))}
      </div>

      {!loading && characters.length === 0 && (
        <div className="text-center py-16 border border-dashed border-slate-800 rounded-2xl">
          <p className="text-slate-400 mb-4">No characters yet</p>
          <Link
            to="/characters/new"
            className="inline-flex px-4 py-2 rounded-lg bg-accent text-sm font-medium"
          >
            Create your first character
          </Link>
        </div>
      )}
    </div>
  );
}
