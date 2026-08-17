import { useEffect, useState, useRef } from "react";
import { Link } from "react-router-dom";
import { useAppStore } from "../../stores/appStore";

export default function PersonaBrowser() {
  const { personas, loading, loadPersonas, defaultPersona, setDefaultPersona, loadDefaultPersona } =
    useAppStore();
  const [search, setSearch] = useState("");
  const fileRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    loadPersonas();
    loadDefaultPersona();
  }, []);

  useEffect(() => {
    const t = setTimeout(() => loadPersonas(search || undefined), 250);
    return () => clearTimeout(t);
  }, [search]);

  async function exportPersona(id: string, name: string) {
    const res = await fetch(`/api/personas/${id}/export`);
    if (!res.ok) {
      alert("Export failed");
      return;
    }
    const blob = await res.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `${name.replace(/\s+/g, "_")}.persona`;
    a.click();
    URL.revokeObjectURL(url);
  }

  async function importPersona(file: File) {
    const fd = new FormData();
    fd.append("file", file);
    const res = await fetch("/api/personas/import", { method: "POST", body: fd });
    if (!res.ok) {
      alert(await res.text());
      return;
    }
    loadPersonas();
  }

  return (
    <div>
      <div className="flex flex-wrap items-center justify-between gap-3 mb-6">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">Personas</h1>
          <p className="text-sm text-slate-400 mt-0.5">
            Who you are in chats. Use {"{{user}}"} in character prompts to insert the active name.
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <input
            ref={fileRef}
            type="file"
            accept=".persona,.zip"
            className="hidden"
            onChange={(e) => {
              const f = e.target.files?.[0];
              if (f) importPersona(f);
              e.target.value = "";
            }}
          />
          <button
            type="button"
            onClick={() => fileRef.current?.click()}
            className="px-3 py-2 rounded-lg bg-surface-800 hover:bg-surface-700 border border-slate-700 text-sm"
          >
            Import .persona
          </button>
          <Link
            to="/personas/new"
            className="px-4 py-2 rounded-lg bg-accent hover:bg-accent-hover text-sm font-medium shadow-lg shadow-accent/20"
          >
            + New Persona
          </Link>
        </div>
      </div>

      <input
        className="w-full max-w-md mb-6 bg-surface-900 border border-slate-700 rounded-lg px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-accent"
        placeholder="Search personas…"
        value={search}
        onChange={(e) => setSearch(e.target.value)}
      />

      {loading && <p className="text-slate-400 text-sm">Loading…</p>}

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        {personas.map((p) => {
          const isDefault = defaultPersona?.id === p.id;
          return (
            <div
              key={p.id}
              className="group bg-surface-900 border border-slate-800 rounded-2xl p-4 hover:border-accent/40 transition"
            >
              <Link to={`/personas/${p.id}`} className="block">
                <div className="flex items-start gap-3">
                  <div className="w-12 h-12 rounded-2xl bg-gradient-to-br from-sky-500/20 to-surface-800 flex items-center justify-center text-lg font-semibold text-sky-300 shrink-0">
                    {p.chat_name.charAt(0).toUpperCase()}
                  </div>
                  <div className="min-w-0">
                    <h3 className="font-medium truncate">
                      {p.profile_name}
                      {isDefault && (
                        <span className="ml-2 text-[10px] uppercase tracking-wide text-accent-muted">
                          Default
                        </span>
                      )}
                    </h3>
                    <p className="text-sm text-slate-400">Chat as: {p.chat_name}</p>
                  </div>
                </div>
              </Link>
              <div className="mt-3 flex flex-wrap gap-2">
                {!isDefault && (
                  <button
                    type="button"
                    onClick={() => setDefaultPersona(p.id)}
                    className="text-xs px-2.5 py-1 rounded-md bg-surface-800 text-slate-300 hover:bg-surface-700"
                  >
                    Set default
                  </button>
                )}
                <button
                  type="button"
                  onClick={() => exportPersona(p.id, p.profile_name)}
                  className="text-xs px-2.5 py-1 rounded-md bg-surface-800 text-slate-300 hover:bg-surface-700"
                >
                  Export
                </button>
                <Link
                  to={`/personas/${p.id}`}
                  className="text-xs px-2.5 py-1 rounded-md bg-surface-800 text-slate-300 hover:bg-surface-700"
                >
                  Edit
                </Link>
                <button
                  type="button"
                  className="text-xs px-2.5 py-1 rounded-md bg-surface-800 text-red-400/80 hover:bg-red-950/40"
                  onClick={async () => {
                    if (!confirm(`Delete persona "${p.profile_name}" permanently?`)) return;
                    await fetch(`/api/personas/${p.id}?hard=true`, { method: "DELETE" });
                    loadPersonas();
                  }}
                >
                  Delete
                </button>
              </div>
            </div>
          );
        })}
      </div>

      {!loading && personas.length === 0 && (
        <div className="text-center py-16 border border-dashed border-slate-800 rounded-2xl">
          <p className="text-slate-400 mb-4">No personas yet</p>
          <Link
            to="/personas/new"
            className="inline-flex px-4 py-2 rounded-lg bg-accent text-sm font-medium"
          >
            Create your first persona
          </Link>
        </div>
      )}
    </div>
  );
}
