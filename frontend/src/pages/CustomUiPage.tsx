import { useState } from "react";
import { useUiPackStore, type UiPack } from "../stores/uiPackStore";
import { FormField, inputClass } from "../components/FormField";

const PRESET_WALLPAPERS = [
  { label: "None", value: "" },
  { label: "Deep night", value: "linear-gradient(160deg, #020617 0%, #1e1b4b 100%)" },
  { label: "Ember", value: "linear-gradient(160deg, #0c0a09 0%, #451a03 100%)" },
  { label: "Forest", value: "linear-gradient(160deg, #052e16 0%, #064e3b 100%)" },
  { label: "Ocean", value: "linear-gradient(160deg, #0b1220 0%, #0c4a6e 100%)" },
  { label: "Soft paper", value: "linear-gradient(180deg, #f8fafc 0%, #e2e8f0 100%)" },
];

export default function CustomUiPage() {
  const {
    packs,
    activePackId,
    chatLayout,
    chatWallpaper,
    setActivePack,
    setChatLayout,
    setChatWallpaper,
    importPack,
    removePack,
    exportActive,
  } = useUiPackStore();

  const [name, setName] = useState("My Hearth UI");
  const [bg, setBg] = useState(
    getComputedStyle(document.documentElement).getPropertyValue("--bg").trim() || "#020617"
  );
  const [bgElevated, setBgElevated] = useState(
    getComputedStyle(document.documentElement).getPropertyValue("--bg-elevated").trim() ||
      "#0f172a"
  );
  const [border, setBorder] = useState(
    getComputedStyle(document.documentElement).getPropertyValue("--border").trim() || "#1e293b"
  );
  const [text, setText] = useState(
    getComputedStyle(document.documentElement).getPropertyValue("--text").trim() || "#e2e8f0"
  );
  const [textMuted, setTextMuted] = useState(
    getComputedStyle(document.documentElement).getPropertyValue("--text-muted").trim() ||
      "#94a3b8"
  );
  const [accent, setAccent] = useState(
    getComputedStyle(document.documentElement).getPropertyValue("--accent").trim() || "#8b5cf6"
  );
  const [font, setFont] = useState("Inter, system-ui, sans-serif");
  const [radius, setRadius] = useState("1rem");
  const [msg, setMsg] = useState<string | null>(null);

  function applyLive() {
    const root = document.documentElement;
    root.style.setProperty("--bg", bg);
    root.style.setProperty("--bg-elevated", bgElevated);
    root.style.setProperty("--border", border);
    root.style.setProperty("--text", text);
    root.style.setProperty("--text-muted", textMuted);
    root.style.setProperty("--accent", accent);
    root.style.setProperty("--accent-hover", accent);
    root.style.setProperty("--accent-muted", accent);
    root.style.setProperty("--font", font);
    root.style.setProperty("--radius", radius);
    document.body.style.fontFamily = font;
  }

  function savePack() {
    applyLive();
    const pack: UiPack = {
      id: `pack-${Date.now().toString(36)}`,
      name: name.trim() || "Untitled UI",
      version: 1,
      description: "Custom Hearth UI pack",
      tokens: {
        bg,
        bgElevated,
        border,
        text,
        textMuted,
        accent,
        accentHover: accent,
        radius,
        font,
        chatWallpaper,
        chatLayout,
      },
    };
    importPack(pack);
    setActivePack(pack.id);
    setMsg(`Saved and activated “${pack.name}”.`);
  }

  function downloadPack() {
    const pack = exportActive() || {
      id: "hearth-export",
      name: name,
      version: 1,
      tokens: {
        bg,
        bgElevated,
        border,
        text,
        textMuted,
        accent,
        font,
        radius,
        chatWallpaper,
        chatLayout,
      },
    };
    const blob = new Blob([JSON.stringify(pack, null, 2)], {
      type: "application/json",
    });
    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = `${(pack.name || "hearth-ui").replace(/\s+/g, "_")}.json`;
    a.click();
  }

  return (
    <div className="max-w-3xl space-y-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">Custom UI</h1>
        <p className="text-sm text-slate-400 mt-1">
          Build your own look, save it as a pack, and import packs from others. Changes apply
          live in this browser.
        </p>
      </div>

      {msg && (
        <div className="text-sm text-emerald-400 border border-emerald-900 bg-emerald-950/30 rounded-lg px-3 py-2">
          {msg}
        </div>
      )}

      <section className="card p-6 space-y-4">
        <h2 className="font-medium">Colors</h2>
        <div className="grid grid-cols-2 sm:grid-cols-3 gap-4">
          {(
            [
              ["Background", bg, setBg],
              ["Elevated / cards", bgElevated, setBgElevated],
              ["Border", border, setBorder],
              ["Text", text, setText],
              ["Muted text", textMuted, setTextMuted],
              ["Accent", accent, setAccent],
            ] as const
          ).map(([label, val, setVal]) => (
            <label key={label} className="text-sm block">
              {label}
              <input
                type="color"
                className="block w-full h-10 mt-1 rounded cursor-pointer bg-transparent"
                value={/^#[0-9a-fA-F]{6}$/.test(val) ? val : "#888888"}
                onChange={(e) => {
                  setVal(e.target.value);
                  setTimeout(applyLive, 0);
                }}
              />
              <input
                className={`${inputClass} mt-1 text-xs`}
                value={val}
                onChange={(e) => {
                  setVal(e.target.value);
                  setTimeout(applyLive, 0);
                }}
              />
            </label>
          ))}
        </div>
        <button type="button" className="btn btn-ghost text-sm" onClick={applyLive}>
          Apply colors now
        </button>
      </section>

      <section className="card p-6 space-y-4">
        <h2 className="font-medium">Typography & shape</h2>
        <FormField label="Font family" example="Inter, system-ui, sans-serif">
          <input
            className={inputClass}
            value={font}
            onChange={(e) => {
              setFont(e.target.value);
              document.body.style.fontFamily = e.target.value;
            }}
          />
        </FormField>
        <FormField label="Corner radius" hint="e.g. 0.5rem · 1rem · 1.25rem">
          <input
            className={inputClass}
            value={radius}
            onChange={(e) => {
              setRadius(e.target.value);
              document.documentElement.style.setProperty("--radius", e.target.value);
            }}
          />
        </FormField>
      </section>

      <section className="card p-6 space-y-4">
        <h2 className="font-medium">Chat layout</h2>
        <div className="flex flex-wrap gap-2">
          {(
            [
              ["classic", "Classic"],
              ["compact", "Compact"],
              ["bubble", "Bubble"],
              ["theater", "Theater"],
            ] as const
          ).map(([id, label]) => (
            <button
              key={id}
              type="button"
              onClick={() => setChatLayout(id)}
              className={`px-3 py-2 rounded-lg border text-sm ${
                chatLayout === id ? "border-accent bg-accent/15" : "border-slate-700"
              }`}
            >
              {label}
            </button>
          ))}
        </div>
      </section>

      <section className="card p-6 space-y-4">
        <h2 className="font-medium">Chat wallpaper</h2>
        <p className="text-xs text-slate-500">
          Any valid CSS background: color, gradient, or url(&quot;…&quot;).
        </p>
        <div className="flex flex-wrap gap-2">
          {PRESET_WALLPAPERS.map((p) => (
            <button
              key={p.label}
              type="button"
              className="text-xs px-2 py-1 rounded-md border border-slate-700 hover:border-accent"
              onClick={() => setChatWallpaper(p.value)}
            >
              {p.label}
            </button>
          ))}
        </div>
        <textarea
          className={`${inputClass} min-h-[80px] font-mono text-xs`}
          value={chatWallpaper}
          onChange={(e) => setChatWallpaper(e.target.value)}
          placeholder='linear-gradient(160deg, #020617, #1e1b4b)'
        />
        <div
          className="h-24 rounded-xl border border-slate-700"
          style={{
            background: chatWallpaper || "var(--bg)",
            backgroundSize: "cover",
          }}
        />
      </section>

      <section className="card p-6 space-y-4">
        <h2 className="font-medium">Save / share pack</h2>
        <FormField label="Pack name" required>
          <input className={inputClass} value={name} onChange={(e) => setName(e.target.value)} />
        </FormField>
        <div className="flex flex-wrap gap-2">
          <button type="button" className="btn btn-primary" onClick={savePack}>
            Save as pack & activate
          </button>
          <button type="button" className="btn btn-ghost" onClick={downloadPack}>
            Export JSON
          </button>
          <label className="btn btn-ghost cursor-pointer">
            Import JSON
            <input
              type="file"
              accept="application/json,.json"
              className="hidden"
              onChange={async (e) => {
                const f = e.target.files?.[0];
                if (!f) return;
                try {
                  const pack = JSON.parse(await f.text()) as UiPack;
                  if (!pack.id || !pack.tokens) throw new Error("Invalid pack: need id + tokens");
                  importPack(pack);
                  setActivePack(pack.id);
                  if (pack.tokens.bg) setBg(pack.tokens.bg);
                  if (pack.tokens.accent) setAccent(pack.tokens.accent);
                  if (pack.tokens.chatWallpaper) setChatWallpaper(pack.tokens.chatWallpaper);
                  if (pack.tokens.chatLayout) setChatLayout(pack.tokens.chatLayout);
                  setMsg(`Imported “${pack.name}”.`);
                } catch (err) {
                  setMsg(String(err));
                }
              }}
            />
          </label>
        </div>
      </section>

      <section className="card p-6 space-y-3">
        <h2 className="font-medium">Saved packs</h2>
        {packs.length === 0 && (
          <p className="text-sm text-slate-500">No packs yet. Save one above.</p>
        )}
        {packs.map((p) => (
          <div
            key={p.id}
            className="flex items-center justify-between gap-2 border border-slate-800 rounded-lg px-3 py-2"
          >
            <div>
              <div className="text-sm font-medium">
                {p.name}
                {activePackId === p.id && (
                  <span className="ml-2 text-[10px] text-accent-muted uppercase">Active</span>
                )}
              </div>
              <div className="text-[11px] text-slate-500">{p.id}</div>
            </div>
            <div className="flex gap-2">
              <button
                type="button"
                className="text-xs text-accent-muted"
                onClick={() => {
                  setActivePack(p.id);
                  setMsg(`Activated “${p.name}”.`);
                }}
              >
                Use
              </button>
              <button
                type="button"
                className="text-xs text-red-400"
                onClick={() => removePack(p.id)}
              >
                Delete
              </button>
            </div>
          </div>
        ))}
      </section>
    </div>
  );
}
