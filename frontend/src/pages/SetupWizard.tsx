import { useState } from "react";
import { setupApi } from "../api/setup";
import type { SetupStatus } from "../types";

interface Props {
  onComplete: (status: SetupStatus) => void;
}

export default function SetupWizard({ onComplete }: Props) {
  const [path, setPath] = useState("");
  const [mode, setMode] = useState<"create" | "open">("create");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function submit() {
    if (!path.trim()) {
      setError("Please enter an absolute path for the data directory.");
      return;
    }
    setBusy(true);
    setError(null);
    try {
      const status =
        mode === "create"
          ? await setupApi.create(path.trim())
          : await setupApi.open(path.trim());
      onComplete(status);
    } catch (e) {
      setError(String(e));
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center p-6">
      <div className="w-full max-w-lg bg-surface-900 border border-slate-800 rounded-xl p-8 shadow-xl">
        <h1 className="text-2xl font-semibold mb-1">Welcome</h1>
        <p className="text-slate-400 text-sm mb-6">
          Choose where Local Character AI will store its database, avatars, and
          backups. Everything stays on your machine.
        </p>

        <div className="flex gap-2 mb-4">
          <button
            type="button"
            onClick={() => setMode("create")}
            className={`flex-1 py-2 rounded-md text-sm font-medium ${
              mode === "create"
                ? "bg-accent text-white"
                : "bg-surface-800 text-slate-300"
            }`}
          >
            Create New Database
          </button>
          <button
            type="button"
            onClick={() => setMode("open")}
            className={`flex-1 py-2 rounded-md text-sm font-medium ${
              mode === "open"
                ? "bg-accent text-white"
                : "bg-surface-800 text-slate-300"
            }`}
          >
            Open Existing
          </button>
        </div>

        <label className="block text-sm text-slate-300 mb-1">
          Data directory (absolute path)
        </label>
        <input
          className="w-full bg-surface-950 border border-slate-700 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-accent"
          placeholder="/home/you/LocalCharacterAI"
          value={path}
          onChange={(e) => setPath(e.target.value)}
        />
        <p className="text-xs text-slate-500 mt-1 mb-4">
          Example:{" "}
          <code className="text-slate-400">D:\AI\LocalCharacterAI</code> or{" "}
          <code className="text-slate-400">~/LocalCharacterAI</code>
        </p>

        {error && (
          <div className="mb-4 text-sm text-red-400 bg-red-950/40 border border-red-900 rounded-md px-3 py-2">
            {error}
          </div>
        )}

        <button
          type="button"
          disabled={busy}
          onClick={submit}
          className="w-full py-2.5 rounded-md bg-accent hover:bg-accent-hover text-white font-medium disabled:opacity-50"
        >
          {busy ? "Working…" : mode === "create" ? "Create & Continue" : "Open & Continue"}
        </button>
      </div>
    </div>
  );
}
