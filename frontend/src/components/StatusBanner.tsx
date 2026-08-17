import { useEffect, useState } from "react";
import { api } from "../api/client";

type Status = "checking" | "ok" | "api-down" | "ollama-down";

/**
 * Lightweight connectivity banner so first-time users know why chat fails.
 */
export default function StatusBanner() {
  const [status, setStatus] = useState<Status>("checking");
  const [model, setModel] = useState<string | null>(null);

  async function check() {
    try {
      await api.get("/health");
    } catch {
      setStatus("api-down");
      return;
    }
    try {
      const c = await api.get<{
        available?: boolean;
        models?: string[];
        default_model?: string;
      }>("/ai/connection");
      if (!c.available || !(c.models && c.models.length)) {
        setStatus("ollama-down");
        setModel(null);
      } else {
        setStatus("ok");
        setModel(c.default_model || c.models[0] || null);
      }
    } catch {
      // Before first-run setup, DB-backed routes may 500 — don't spam Ollama warning
      setStatus("ok");
    }
  }

  useEffect(() => {
    check();
    const t = setInterval(check, 20000);
    return () => clearInterval(t);
  }, []);

  if (status === "checking" || status === "ok") {
    return null;
  }

  if (status === "api-down") {
    return (
      <div className="bg-red-950/80 border-b border-red-800 text-red-100 text-sm px-3 py-2 text-center">
        Backend offline — start the API window (or run <code className="text-xs">python run.py</code> in{" "}
        <code className="text-xs">backend/</code>).{" "}
        <button type="button" className="underline ml-1" onClick={check}>
          Retry
        </button>
      </div>
    );
  }

  return (
    <div className="bg-amber-950/70 border-b border-amber-800 text-amber-100 text-sm px-3 py-2 text-center">
      Ollama not detected or no models installed. Install from{" "}
      <a className="underline" href="https://ollama.com" target="_blank" rel="noreferrer">
        ollama.com
      </a>
      , then run <code className="text-xs">ollama pull llama3.2</code> and set the model in Settings.{" "}
      <button type="button" className="underline ml-1" onClick={check}>
        Retry
      </button>
      {model ? <span className="ml-2 opacity-70">({model})</span> : null}
    </div>
  );
}
