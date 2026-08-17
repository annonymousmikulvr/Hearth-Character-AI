import { useEffect, useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { useAppStore } from "../../stores/appStore";
import { conversationsApi } from "../../api/conversations";
import { api } from "../../api/client";
import { FormField, inputClass } from "../../components/FormField";

export default function ChatCreate() {
  const navigate = useNavigate();
  const [params] = useSearchParams();
  const {
    characters,
    personas,
    defaultPersona,
    loadCharacters,
    loadPersonas,
    loadDefaultPersona,
  } = useAppStore();

  const [characterId, setCharacterId] = useState(params.get("character") || "");
  const [personaId, setPersonaId] = useState("");
  const [displayName, setDisplayName] = useState("");
  const [title, setTitle] = useState("");
  const [mode, setMode] = useState<"standard" | "custom">("standard");
  const [seedNotes, setSeedNotes] = useState("");
  const [seedScript, setSeedScript] = useState("");
  const [situation, setSituation] = useState("");
  const [generatingPreset, setGeneratingPreset] = useState(false);
  const [presetSource, setPresetSource] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [worldId, setWorldId] = useState("");
  const [worlds, setWorlds] = useState<{id:string;name:string}[]>([]);

  useEffect(() => {
    loadCharacters();
    loadPersonas();
    loadDefaultPersona();
    api.get<{id:string;name:string}[]>('/worlds').then(setWorlds).catch(() => {});
  }, []);

  useEffect(() => {
    if (defaultPersona && !personaId) {
      setPersonaId(defaultPersona.id);
      setDisplayName(defaultPersona.chat_name);
    }
  }, [defaultPersona]);

  useEffect(() => {
    const p = personas.find((x) => x.id === personaId);
    if (p && !displayName) setDisplayName(p.chat_name);
  }, [personaId, personas]);

  async function generatePreset() {
    if (!characterId || !personaId) {
      setError("Select a character and persona first.");
      return;
    }
    setGeneratingPreset(true);
    setError(null);
    setPresetSource(null);
    try {
      const res = await api.post<{
        seed_script: string;
        seed_notes: string;
        source: string;
        character_name: string;
        user_name: string;
      }>("/conversations/generate-preset", {
        character_id: characterId,
        persona_id: personaId,
        situation: situation.trim() || undefined,
      });
      setSeedScript(res.seed_script);
      setSeedNotes(res.seed_notes);
      setPresetSource(res.source);
    } catch (e) {
      setError(String(e));
    } finally {
      setGeneratingPreset(false);
    }
  }

  function parseSeedScript(script: string) {
    // Lines: User: ... / Char: ... / System: ...
    const messages: { role: string; content: string }[] = [];
    for (const line of script.split("\n")) {
      const m = line.match(/^\s*(user|char|character|assistant|system)\s*:\s*(.+)$/i);
      if (!m) continue;
      let role = m[1].toLowerCase();
      if (role === "char" || role === "character") role = "assistant";
      messages.push({ role, content: m[2].trim() });
    }
    return messages;
  }

  async function startChat() {
    if (!characterId || !personaId) {
      setError("Select both a character and a persona.");
      return;
    }
    setBusy(true);
    setError(null);
    try {
      const seed_messages =
        mode === "custom" ? parseSeedScript(seedScript) : undefined;
      const conv = await conversationsApi.create({
        character_id: characterId,
        persona_id: personaId,
        persona_display_name: displayName.trim() || undefined,
        title: title.trim() || undefined,
        seed_notes: mode === "custom" ? seedNotes.trim() || undefined : undefined,
        is_custom: mode === "custom",
        seed_messages,
        world_id: worldId || undefined,
      } as any);
      navigate(`/chats/${conv.id}`);
    } catch (e) {
      setError(String(e));
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="max-w-xl space-y-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">New Chat</h1>
        <p className="text-sm text-slate-400 mt-1">
          Tokens like <code className="text-accent-muted">{"{{user}}"}</code> and{" "}
          <code className="text-accent-muted">{"{{char}}"}</code> expand to the
          active names in prompts.
        </p>
      </div>

      <div className="flex gap-2 p-1 bg-surface-900 rounded-xl border border-slate-800">
        <button
          type="button"
          onClick={() => setMode("standard")}
          className={`flex-1 py-2 rounded-lg text-sm font-medium transition ${
            mode === "standard" ? "bg-accent text-white shadow" : "text-slate-400"
          }`}
        >
          Standard
        </button>
        <button
          type="button"
          onClick={() => setMode("custom")}
          className={`flex-1 py-2 rounded-lg text-sm font-medium transition ${
            mode === "custom" ? "bg-accent text-white shadow" : "text-slate-400"
          }`}
        >
          Custom chat
        </button>
      </div>

      {error && (
        <div className="text-sm text-red-400 bg-red-950/40 border border-red-900 rounded-lg px-3 py-2">
          {error}
        </div>
      )}

      <section className="bg-surface-900 border border-slate-800 rounded-2xl p-6 space-y-5">
        <FormField
          label="Character"
          required
          description="Who the AI is in this conversation."
        >
          <select
            className={inputClass}
            value={characterId}
            onChange={(e) => setCharacterId(e.target.value)}
          >
            <option value="">— Select Character —</option>
            {characters.map((c) => (
              <option key={c.id} value={c.id}>
                {c.name}
              </option>
            ))}
          </select>
        </FormField>

        <FormField label="Persona" required description="Who you are.">
          <select
            className={inputClass}
            value={personaId}
            onChange={(e) => {
              setPersonaId(e.target.value);
              const p = personas.find((x) => x.id === e.target.value);
              if (p) setDisplayName(p.chat_name);
            }}
          >
            <option value="">— Select Persona —</option>
            {personas.map((p) => (
              <option key={p.id} value={p.id}>
                {p.profile_name} ({p.chat_name})
                {defaultPersona?.id === p.id ? " — default" : ""}
              </option>
            ))}
          </select>
        </FormField>

        <FormField
          label="Display Name"
          description="Name shown for you in this chat. Replaces {{user}}."
          example="Alex"
        >
          <input
            className={inputClass}
            value={displayName}
            onChange={(e) => setDisplayName(e.target.value)}
          />
        </FormField>

        <FormField label="Title (optional)">
          <input
            className={inputClass}
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            placeholder="Evening at the tavern"
          />
        </FormField>

        <FormField label="World (optional)" description="Attach a world so lore and rules stay consistent.">
          <select className={inputClass} value={worldId} onChange={(e) => setWorldId(e.target.value)}>
            <option value="">— None —</option>
            {worlds.map((w) => (
              <option key={w.id} value={w.id}>{w.name}</option>
            ))}
          </select>
        </FormField>

        {mode === "custom" && (
          <>
            <FormField
              label="Situation (for auto-preset)"
              description="Optional. Tells the generator how the chat starts. Leave blank for a casual run-in."
              example="Reunited after three years, rain just started"
            >
              <input
                className={inputClass}
                value={situation}
                onChange={(e) => setSituation(e.target.value)}
                placeholder="Casual meeting / argument / reunion…"
              />
            </FormField>
            <button
              type="button"
              disabled={generatingPreset || !characterId || !personaId}
              onClick={generatePreset}
              className="w-full py-2.5 rounded-xl border border-accent/40 bg-accent/10 hover:bg-accent/20 text-accent-muted text-sm font-medium disabled:opacity-40"
            >
              {generatingPreset
                ? "Generating preset…"
                : "Auto-generate chat preset from Character + Persona"}
            </button>
            {presetSource && (
              <p className="text-xs text-slate-500">
                Filled from {presetSource === "model" ? "local model" : "template"} — edit anything below before starting.
              </p>
            )}
            <FormField
              label="Custom context / seed"
              description="Backstory or situation injected for this chat only. Supports {{user}} and {{char}}. Editable after auto-generate."
            >
              <textarea
                className={`${inputClass} min-h-[100px]`}
                value={seedNotes}
                onChange={(e) => setSeedNotes(e.target.value)}
                placeholder="You meet {{char}} again after three years apart. The rain has just started."
              />
            </FormField>
            <FormField
              label="Seed messages (chat preset)"
              description={'One per line: Char: … / User: … / System: … Use {{char}} and {{user}}. Example: Char: *{{char}} approaches {{user}}.* — "Hey {{user}}"'}
              example={'Char: *{{char}} touches {{user}}\'s shoulder.* — "Hey {{user}}, what\'s up?"'}
            >
              <textarea
                className={`${inputClass} min-h-[160px] font-mono text-xs`}
                value={seedScript}
                onChange={(e) => setSeedScript(e.target.value)}
                placeholder={'Char: *{{char}} approaches {{user}} and touches their shoulder.* — "Hey {{user}}, what\'s up?"\nUser: — "Hey {{char}}, nothin\' much. What about you?"'}
              />
            </FormField>
          </>
        )}
      </section>

      <button
        type="button"
        onClick={startChat}
        disabled={busy || !characterId || !personaId}
        className="w-full py-3 rounded-xl bg-accent hover:bg-accent-hover text-white font-medium disabled:opacity-40 shadow-lg shadow-accent/25"
      >
        {busy ? "Creating…" : mode === "custom" ? "Start Custom Chat" : "Start Chat"}
      </button>
    </div>
  );
}
