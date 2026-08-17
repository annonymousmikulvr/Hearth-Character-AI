import { useEffect, useState } from "react";
import { useAppStore } from "../stores/appStore";
import { settingsApi } from "../api/settings";
import { aiApi, type AIConnection } from "../api/ai";
import { FormField, inputClass } from "../components/FormField";
import { useThemeStore, THEMES, type ThemeId } from "../stores/themeStore";
import { useDevStore } from "../stores/devStore";

export default function SettingsPage() {
  const theme = useThemeStore((s) => s.theme);
  const setTheme = useThemeStore((s) => s.setTheme);
  const devMode = useDevStore((s) => s.devMode);
  const setDevMode = useDevStore((s) => s.setDevMode);

  const {
    defaultPersona,
    loadDefaultPersona,
    setDefaultPersona,
    personas,
    loadPersonas,
  } = useAppStore();

  const [connection, setConnection] = useState<AIConnection | null>(null);
  const [defaultModel, setDefaultModel] = useState("");
  const [temperature, setTemperature] = useState("0.85");
  const [maxTokens, setMaxTokens] = useState("512");
  const [ollamaUrl, setOllamaUrl] = useState("http://127.0.0.1:11434");
  const [testResult, setTestResult] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [msg, setMsg] = useState<string | null>(null);
  const [historyLimit, setHistoryLimit] = useState("24");
  const [speed, setSpeed] = useState("balanced");

  async function refreshConnection() {
    try {
      const c = await aiApi.connection();
      setConnection(c);
      setDefaultModel(c.default_model || "");
      setOllamaUrl(c.base_url);
    } catch (e) {
      setConnection(null);
      console.error(e);
    }
  }

  useEffect(() => {
    loadDefaultPersona();
    loadPersonas();
    refreshConnection();
    settingsApi
      .getAll()
      .then((s) => {
        if (s.default_temperature) setTemperature(s.default_temperature);
        if (s.default_max_tokens) setMaxTokens(s.default_max_tokens);
        if (s.ollama_base_url) setOllamaUrl(s.ollama_base_url);
        if (s.default_model) setDefaultModel(s.default_model);
        if (s.history_limit) setHistoryLimit(s.history_limit);
        if (s.generation_speed) setSpeed(s.generation_speed);
      })
      .catch(console.error);
  }, []);

  async function putSetting(key: string, value: string) {
    await fetch(`/api/settings/${key}`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ value }),
    });
  }

  async function saveAI() {
    setBusy(true);
    setMsg(null);
    try {
      await aiApi.config({
        ollama_base_url: ollamaUrl.trim(),
        default_model: defaultModel.trim(),
        default_temperature: parseFloat(temperature) || 0.85,
        default_max_tokens: parseInt(maxTokens, 10) || 512,
      });
      await putSetting("history_limit", historyLimit);
      await putSetting("generation_speed", speed);
      await refreshConnection();
      setMsg("Settings saved.");
    } catch (e) {
      setMsg(String(e));
    } finally {
      setBusy(false);
    }
  }

  async function runTest() {
    setBusy(true);
    setTestResult(null);
    try {
      const r = await aiApi.test({
        model: defaultModel || undefined,
        prompt: 'Reply with exactly: — "Hearth is online."',
      });
      setTestResult(r.ok ? `OK (${r.latency_ms}ms): ${r.response}` : `Failed: ${r.error}`);
    } catch (e) {
      setTestResult(String(e));
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="max-w-2xl space-y-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">Settings</h1>
        <p className="text-sm text-slate-400 mt-1">Hearth · local-first preferences</p>
      </div>

      {msg && (
        <div className="text-sm text-emerald-400 bg-emerald-950/30 border border-emerald-900 rounded-lg px-3 py-2">
          {msg}
        </div>
      )}

      {/* Dev mode — prominent */}
      <section className="bg-surface-900 border border-slate-800 rounded-xl p-6 space-y-4">
        <div className="flex items-center justify-between gap-4">
          <div>
            <h2 className="text-lg font-medium">Developer mode</h2>
            <p className="text-sm text-slate-400 mt-1">
              Enable slash commands in chats. Type <code className="text-accent-muted">/help</code> for the list.
            </p>
          </div>
          <button
            type="button"
            role="switch"
            aria-checked={devMode}
            onClick={() => setDevMode(!devMode)}
            className={`relative w-14 h-8 rounded-full transition shrink-0 ${
              devMode ? "bg-accent" : "bg-slate-700"
            }`}
          >
            <span
              className={`absolute top-1 left-1 w-6 h-6 rounded-full bg-white transition ${
                devMode ? "translate-x-6" : ""
              }`}
            />
          </button>
        </div>
        {devMode && (
          <div className="text-xs text-slate-400 bg-surface-950 border border-slate-800 rounded-lg p-3 space-y-1">
            <div className="font-medium text-slate-300 mb-1">Dev mode is ON</div>
            <div>/side · /side_gen · /backstory · /memory add|list · /vars · /ping · /regen</div>
          </div>
        )}
      </section>

      <section className="bg-surface-900 border border-slate-800 rounded-xl p-6 space-y-4">
        <h2 className="text-lg font-medium">Theme</h2>
        <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
          {THEMES.map((th) => (
            <button
              key={th.id}
              type="button"
              onClick={() => setTheme(th.id as ThemeId)}
              className={`text-left px-3 py-2.5 rounded-xl border text-sm transition ${
                theme === th.id
                  ? "border-accent bg-accent/15"
                  : "border-slate-700 hover:border-slate-500"
              }`}
            >
              <div className="font-medium">{th.label}</div>
              <div className="text-xs text-slate-400">{th.description}</div>
            </button>
          ))}
        </div>
        <div className="grid grid-cols-2 gap-3 pt-2">
          <label className="text-sm">
            Custom accent
            <input
              type="color"
              className="block w-full h-10 mt-1 rounded cursor-pointer bg-transparent"
              defaultValue={localStorage.getItem("lcai-custom-accent") || "#8b5cf6"}
              onChange={(e) => {
                document.documentElement.style.setProperty("--accent", e.target.value);
                document.documentElement.style.setProperty("--accent-hover", e.target.value);
                document.documentElement.style.setProperty("--accent-muted", e.target.value);
                localStorage.setItem("lcai-custom-accent", e.target.value);
              }}
            />
          </label>
          <label className="text-sm">
            Custom background
            <input
              type="color"
              className="block w-full h-10 mt-1 rounded cursor-pointer bg-transparent"
              defaultValue={localStorage.getItem("lcai-custom-bg") || "#020617"}
              onChange={(e) => {
                document.documentElement.style.setProperty("--bg", e.target.value);
                localStorage.setItem("lcai-custom-bg", e.target.value);
              }}
            />
          </label>
        </div>
      </section>

      <section className="bg-surface-900 border border-slate-800 rounded-xl p-6 space-y-4">
        <h2 className="text-lg font-medium">Generation speed</h2>
        <div className="flex flex-wrap gap-2">
          {(["fast", "balanced", "quality"] as const).map((s) => (
            <button
              key={s}
              type="button"
              onClick={() => setSpeed(s)}
              className={`px-3 py-2 rounded-lg border text-sm capitalize ${
                speed === s ? "border-accent bg-accent/15" : "border-slate-700"
              }`}
            >
              {s}
            </button>
          ))}
        </div>
        <FormField label="History limit (messages)" description="Lower is faster. Default 24.">
          <input
            className={inputClass}
            type="number"
            min={6}
            max={100}
            value={historyLimit}
            onChange={(e) => setHistoryLimit(e.target.value)}
          />
        </FormField>
      </section>

      <section className="bg-surface-900 border border-slate-800 rounded-xl p-6 space-y-4">
        <h2 className="text-lg font-medium">Default persona</h2>
        <p className="text-sm text-slate-400">
          New chats use this persona unless you override it.
        </p>
        <select
          className={inputClass}
          value={defaultPersona?.id ?? ""}
          onChange={(e) => setDefaultPersona(e.target.value || null)}
        >
          <option value="">— None —</option>
          {personas.map((p) => (
            <option key={p.id} value={p.id}>
              {p.profile_name} ({p.chat_name})
            </option>
          ))}
        </select>
      </section>


      <section className="bg-surface-900 border border-slate-800 rounded-xl p-6 space-y-4">
        <h2 className="text-lg font-medium">Image generation (optional)</h2>
        <p className="text-sm text-slate-400">
          Connect a local Automatic1111 / SD WebUI API if you have Stable Diffusion installed.
          Not required for chat.
        </p>
        <label className="flex items-center gap-2 text-sm">
          <input
            type="checkbox"
            defaultChecked={false}
            onChange={async (e) => {
              await putSetting("image_backend_enabled", e.target.checked ? "true" : "false");
              setMsg(e.target.checked ? "Image backend enabled" : "Image backend disabled");
            }}
          />
          Enable image backend
        </label>
        <FormField label="Backend URL" example="http://127.0.0.1:7860">
          <input
            className={inputClass}
            placeholder="http://127.0.0.1:7860"
            onBlur={async (e) => {
              if (e.target.value.trim()) await putSetting("image_backend_url", e.target.value.trim());
            }}
          />
        </FormField>
      </section>

      <section className="bg-surface-900 border border-slate-800 rounded-xl p-6 space-y-5">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-medium">Local AI (Ollama)</h2>
          <span
            className={`text-xs px-2 py-0.5 rounded-full ${
              connection?.available
                ? "bg-emerald-950 text-emerald-400 border border-emerald-800"
                : "bg-red-950 text-red-400 border border-red-800"
            }`}
          >
            {connection?.available ? "Connected" : "Not connected"}
          </span>
        </div>

        <FormField label="Ollama URL" example="http://127.0.0.1:11434">
          <input
            className={inputClass}
            value={ollamaUrl}
            onChange={(e) => setOllamaUrl(e.target.value)}
          />
        </FormField>

        <FormField label="Default model">
          <select
            className={inputClass}
            value={defaultModel}
            onChange={(e) => setDefaultModel(e.target.value)}
          >
            <option value="">— Select —</option>
            {(connection?.models || []).map((m) => (
              <option key={m} value={m}>
                {m}
              </option>
            ))}
          </select>
        </FormField>

        <div className="grid grid-cols-2 gap-3">
          <FormField label="Temperature" hint="0–2">
            <input
              className={inputClass}
              value={temperature}
              onChange={(e) => setTemperature(e.target.value)}
            />
          </FormField>
          <FormField label="Max tokens" hint="16–8192">
            <input
              className={inputClass}
              value={maxTokens}
              onChange={(e) => setMaxTokens(e.target.value)}
            />
          </FormField>
        </div>

        <div className="flex flex-wrap gap-2">
          <button
            type="button"
            onClick={saveAI}
            disabled={busy}
            className="px-4 py-2 rounded-lg bg-accent hover:bg-accent-hover text-sm font-medium disabled:opacity-40"
          >
            Save
          </button>
          <button
            type="button"
            onClick={runTest}
            disabled={busy}
            className="px-4 py-2 rounded-lg border border-slate-700 text-sm hover:border-slate-500 disabled:opacity-40"
          >
            Test generation
          </button>
          <button
            type="button"
            onClick={refreshConnection}
            className="px-4 py-2 rounded-lg border border-slate-700 text-sm hover:border-slate-500"
          >
            Refresh models
          </button>
        </div>
        {testResult && (
          <pre className="text-xs bg-surface-950 border border-slate-800 rounded-lg p-3 whitespace-pre-wrap">
            {testResult}
          </pre>
        )}
      </section>
    </div>
  );
}
