import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { personasApi } from "../../api/personas";
import type { Persona } from "../../types";
import { FormField, inputClass } from "../../components/FormField";

const empty: Partial<Persona> = {
  profile_name: "",
  chat_name: "",
  traits: [],
  likes: [],
  dislikes: [],
  habits: [],
  additional_facts: [],
  tags: [],
  example_dialogues: [],
};

function listToInput(arr: string[] | undefined): string {
  return (arr || []).join(", ");
}

function inputToList(s: string): string[] {
  return s
    .split(",")
    .map((t) => t.trim())
    .filter(Boolean);
}

export default function PersonaEditor() {
  const { id } = useParams();
  const isNew = !id || id === "new";
  const navigate = useNavigate();
  const [form, setForm] = useState<Partial<Persona>>(empty);
  const [tagsInput, setTagsInput] = useState("");
  const [traitsInput, setTraitsInput] = useState("");
  const [likesInput, setLikesInput] = useState("");
  const [dislikesInput, setDislikesInput] = useState("");
  const [habitsInput, setHabitsInput] = useState("");
  const [factsInput, setFactsInput] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [openness, setOpenness] = useState(50);
  const [warmth, setWarmth] = useState(50);
  const [assertiveness, setAssertiveness] = useState(50);
  const [humor, setHumor] = useState(40);

  useEffect(() => {
    if (!isNew && id) {
      personasApi
        .get(id)
        .then((p) => {
          setForm(p);
          setTagsInput(listToInput(p.tags));
          setTraitsInput(listToInput(p.traits));
          setLikesInput(listToInput(p.likes));
          setDislikesInput(listToInput(p.dislikes));
          setHabitsInput(listToInput(p.habits));
          setFactsInput(listToInput(p.additional_facts));
        })
        .catch((e) => setError(String(e)));
    }
  }, [id, isNew]);

  function update<K extends keyof Persona>(key: K, value: Persona[K]) {
    setForm((f) => ({ ...f, [key]: value }));
  }

  async function save() {
    if (!form.profile_name?.trim() || !form.chat_name?.trim()) {
      setError("Profile name and chat name are required");
      return;
    }
    setBusy(true);
    setError(null);
    const scaleNote =
      `Personality scales: openness ${openness}/100, warmth ${warmth}/100, assertiveness ${assertiveness}/100, humor ${humor}/100.`;
    const baseCustom = (form.custom_instructions || "").replace(/Personality scales:.*$/m, "").trim();
    const payload = {
      ...form,
      custom_instructions: [baseCustom, scaleNote].filter(Boolean).join("\n"),
      tags: inputToList(tagsInput),
      traits: inputToList(traitsInput),
      likes: inputToList(likesInput),
      dislikes: inputToList(dislikesInput),
      habits: inputToList(habitsInput),
      additional_facts: inputToList(factsInput),
    };
    try {
      if (isNew) {
        await personasApi.create(payload);
      } else {
        await personasApi.update(id!, payload);
      }
      navigate("/personas");
    } catch (e) {
      setError(String(e));
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="max-w-3xl space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold">
            {isNew ? "New Persona" : "Edit Persona"}
          </h1>
          <p className="text-sm text-slate-400 mt-1">
            Personas define who <em>you</em> are in a conversation. One persona
            can be used across many chats with different display names.
          </p>
        </div>
        <button
          type="button"
          onClick={() => navigate("/personas")}
          className="text-sm text-slate-400 hover:text-white"
        >
          Cancel
        </button>
      </div>

      {error && (
        <div className="text-sm text-red-400 bg-red-950/40 border border-red-900 rounded-md px-3 py-2">
          {error}
        </div>
      )}

      {/* Identity */}
      <section className="bg-surface-900 border border-slate-800 rounded-xl p-6 space-y-5">
        <h2 className="font-medium text-slate-200">Identity</h2>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-5">
          <FormField
            label="Profile Name"
            required
            description="Your full identity name. Used in settings and persona lists."
            example="Alexander Johnson"
          >
            <input
              className={inputClass}
              value={form.profile_name || ""}
              onChange={(e) => update("profile_name", e.target.value)}
              placeholder="Alexander Johnson"
            />
          </FormField>

          <FormField
            label="Chat Name"
            required
            description="The name shown inside conversations by default. Can be overridden per chat."
            example="Alex"
          >
            <input
              className={inputClass}
              value={form.chat_name || ""}
              onChange={(e) => update("chat_name", e.target.value)}
              placeholder="Alex"
            />
          </FormField>

          <FormField
            label="Age"
            description="Optional age of this persona."
            hint="Min 0 · Max 200"
            example="28"
          >
            <input
              type="number"
              min={0}
              max={200}
              className={inputClass}
              value={form.age ?? ""}
              onChange={(e) =>
                update(
                  "age",
                  e.target.value ? parseInt(e.target.value, 10) : null
                )
              }
              placeholder="28"
            />
          </FormField>

          <FormField
            label="Pronouns"
            description="How this persona should be referred to."
            example="he/him"
          >
            <input
              className={inputClass}
              value={form.pronouns || ""}
              onChange={(e) => update("pronouns", e.target.value)}
              placeholder="he/him"
            />
          </FormField>
        </div>
      </section>

      {/* Appearance */}
      <section className="bg-surface-900 border border-slate-800 rounded-xl p-6 space-y-5">
        <h2 className="font-medium text-slate-200">Appearance</h2>

        <FormField
          label="Appearance Description"
          description="Free-form summary of how this persona looks. Preferred over filling every detail field."
          example="Tall, lean build, short dark hair, green eyes, usually wears a weathered leather jacket."
        >
          <textarea
            className={`${inputClass} min-h-[72px]`}
            value={form.appearance_description || ""}
            onChange={(e) =>
              update("appearance_description", e.target.value)
            }
            placeholder="Tall, lean build, short dark hair…"
          />
        </FormField>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-5">
          <FormField
            label="Height"
            description="Optional height detail."
            example="6'1&quot; / 185 cm"
          >
            <input
              className={inputClass}
              value={form.height || ""}
              onChange={(e) => update("height", e.target.value)}
              placeholder='6&apos;1" / 185 cm'
            />
          </FormField>
          <FormField
            label="Build"
            description="Optional body type."
            example="Lean / athletic"
          >
            <input
              className={inputClass}
              value={form.build || ""}
              onChange={(e) => update("build", e.target.value)}
              placeholder="Lean / athletic"
            />
          </FormField>
          <FormField
            label="Hair"
            description="Colour, length, style."
            example="Short dark brown, slightly messy"
          >
            <input
              className={inputClass}
              value={form.hair || ""}
              onChange={(e) => update("hair", e.target.value)}
              placeholder="Short dark brown, slightly messy"
            />
          </FormField>
          <FormField
            label="Eyes"
            description="Colour and expression."
            example="Green, often amused"
          >
            <input
              className={inputClass}
              value={form.eyes || ""}
              onChange={(e) => update("eyes", e.target.value)}
              placeholder="Green, often amused"
            />
          </FormField>
          <FormField
            label="Skin"
            description="Tone or other notes."
            example="Light olive"
          >
            <input
              className={inputClass}
              value={form.skin || ""}
              onChange={(e) => update("skin", e.target.value)}
              placeholder="Light olive"
            />
          </FormField>
          <FormField
            label="Clothing"
            description="Typical outfit or style."
            example="Weathered leather jacket, dark jeans"
          >
            <input
              className={inputClass}
              value={form.clothing || ""}
              onChange={(e) => update("clothing", e.target.value)}
              placeholder="Weathered leather jacket, dark jeans"
            />
          </FormField>
        </div>
      </section>

      {/* Personality */}
      <section className="bg-surface-900 border border-slate-800 rounded-xl p-6 space-y-5">
        <h2 className="font-medium text-slate-200">Personality</h2>

        <FormField
          label="Traits"
          description="Comma-separated personality traits."
          example="curious, witty, loyal"
        >
          <input
            className={inputClass}
            value={traitsInput}
            onChange={(e) => setTraitsInput(e.target.value)}
            placeholder="curious, witty, loyal"
          />
        </FormField>

        <FormField
          label="Personality Description"
          description="Longer free-form personality summary."
          example="Curious about the world, quick with a joke, but fiercely loyal to friends."
        >
          <textarea
            className={`${inputClass} min-h-[80px]`}
            value={form.personality_description || ""}
            onChange={(e) =>
              update("personality_description", e.target.value)
            }
            placeholder="Curious about the world, quick with a joke…"
          />
        </FormField>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-5">
          <FormField
            label="Likes"
            description="Comma-separated things this persona enjoys."
            example="rainy nights, old maps, strong coffee"
          >
            <input
              className={inputClass}
              value={likesInput}
              onChange={(e) => setLikesInput(e.target.value)}
              placeholder="rainy nights, old maps, strong coffee"
            />
          </FormField>
          <FormField
            label="Dislikes"
            description="Comma-separated things this persona avoids."
            example="crowds, small talk, being late"
          >
            <input
              className={inputClass}
              value={dislikesInput}
              onChange={(e) => setDislikesInput(e.target.value)}
              placeholder="crowds, small talk, being late"
            />
          </FormField>
        </div>

        <FormField
          label="Habits"
          description="Comma-separated recurring behaviours."
          example="taps fingers when thinking, always carries a notebook"
        >
          <input
            className={inputClass}
            value={habitsInput}
            onChange={(e) => setHabitsInput(e.target.value)}
            placeholder="taps fingers when thinking, always carries a notebook"
          />
        </FormField>

        <FormField
          label="Speaking Style"
          description="How this persona tends to talk."
          example="Casual, warm, occasional dry humour"
        >
          <input
            className={inputClass}
            value={form.speaking_style || ""}
            onChange={(e) => update("speaking_style", e.target.value)}
            placeholder="Casual, warm, occasional dry humour"
          />
        </FormField>
      </section>

      {/* Background */}
      <section className="bg-surface-900 border border-slate-800 rounded-xl p-6 space-y-5">
        <h2 className="font-medium text-slate-200">Background</h2>

        <FormField
          label="Biography"
          description="Life history, origin, and important past events."
          example="Grew up in a coastal town, left at 19 to study cartography…"
        >
          <textarea
            className={`${inputClass} min-h-[80px]`}
            value={form.biography || ""}
            onChange={(e) => update("biography", e.target.value)}
            placeholder="Grew up in a coastal town…"
          />
        </FormField>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-5">
          <FormField
            label="Occupation"
            description="Current or typical job / role."
            example="Cartographer"
          >
            <input
              className={inputClass}
              value={form.occupation || ""}
              onChange={(e) => update("occupation", e.target.value)}
              placeholder="Cartographer"
            />
          </FormField>
          <FormField
            label="Location"
            description="Where this persona usually is."
            example="Port city of Eldoria"
          >
            <input
              className={inputClass}
              value={form.location || ""}
              onChange={(e) => update("location", e.target.value)}
              placeholder="Port city of Eldoria"
            />
          </FormField>
        </div>

        <FormField
          label="Additional Facts"
          description="Comma-separated facts the AI should know about this persona."
          example="allergic to cats, plays guitar, has a scar on left hand"
        >
          <input
            className={inputClass}
            value={factsInput}
            onChange={(e) => setFactsInput(e.target.value)}
            placeholder="allergic to cats, plays guitar, has a scar on left hand"
          />
        </FormField>

        <FormField
          label="Tags"
          description="Comma-separated labels for filtering."
          example="default, modern, traveler"
        >
          <input
            className={inputClass}
            value={tagsInput}
            onChange={(e) => setTagsInput(e.target.value)}
            placeholder="default, modern, traveler"
          />
        </FormField>
      </section>

      
      <section className="bg-surface-900 border border-slate-800 rounded-xl p-6 space-y-5">
        <h2 className="font-medium text-slate-200">Personality scales</h2>
        <p className="text-xs text-slate-500 -mt-2">
          These guide how the AI plays this persona when you are roleplaying as them or when facts are recalled.
        </p>
        {(
          [
            ["Openness", openness, setOpenness, "Curious vs reserved"],
            ["Warmth", warmth, setWarmth, "Friendly vs cool"],
            ["Assertiveness", assertiveness, setAssertiveness, "Direct vs soft"],
            ["Humor", humor, setHumor, "Playful vs serious"],
          ] as const
        ).map(([label, val, setVal, hint]) => (
          <label key={label} className="block">
            <div className="flex justify-between text-sm mb-1">
              <span>{label}</span>
              <span className="text-slate-400">{val}</span>
            </div>
            <input
              type="range"
              min={0}
              max={100}
              value={val}
              onChange={(e) => setVal(parseInt(e.target.value, 10))}
              className="w-full accent-[var(--accent)]"
            />
            <span className="text-xs text-slate-500">{hint}</span>
          </label>
        ))}
        <div className="flex flex-wrap gap-2 pt-2">
          <button type="button" className="btn btn-ghost text-xs" onClick={() => { setOpenness(70); setWarmth(70); setHumor(60); setAssertiveness(40); }}>
            Friendly preset
          </button>
          <button type="button" className="btn btn-ghost text-xs" onClick={() => { setOpenness(40); setWarmth(30); setHumor(20); setAssertiveness(75); }}>
            Stoic preset
          </button>
          <button type="button" className="btn btn-ghost text-xs" onClick={() => { setOpenness(80); setWarmth(50); setHumor(80); setAssertiveness(55); }}>
            Witty preset
          </button>
        </div>
      </section>

      {/* Behaviour */}
      <section className="bg-surface-900 border border-slate-800 rounded-xl p-6 space-y-5">
        <h2 className="font-medium text-slate-200">Behaviour</h2>

        <FormField
          label="How They Act"
          description="General behaviour and body language in scenes."
          example="Stands with arms crossed when thinking; leans in when interested."
        >
          <textarea
            className={`${inputClass} min-h-[72px]`}
            value={form.how_they_act || ""}
            onChange={(e) => update("how_they_act", e.target.value)}
            placeholder="Stands with arms crossed when thinking…"
          />
        </FormField>

        <FormField
          label="How They Respond"
          description="How this persona tends to react in conversation."
          example="Answers questions directly, then adds a personal observation."
        >
          <textarea
            className={`${inputClass} min-h-[72px]`}
            value={form.how_they_respond || ""}
            onChange={(e) => update("how_they_respond", e.target.value)}
            placeholder="Answers questions directly, then adds a personal observation."
          />
        </FormField>

        <FormField
          label="Custom Instructions"
          description="Extra instructions for the model about this persona. Highest priority persona guidance."
          example="Never reveal the persona's full legal name unless asked. Prefer short replies."
        >
          <textarea
            className={`${inputClass} min-h-[72px]`}
            value={form.custom_instructions || ""}
            onChange={(e) => update("custom_instructions", e.target.value)}
            placeholder="Never reveal the persona's full legal name unless asked…"
          />
        </FormField>
      </section>

      
      <section className="bg-surface-900 border border-slate-800 rounded-xl p-6 space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="font-medium text-slate-200">Family tree</h2>
            <p className="text-xs text-slate-500">
              Relatives the character should know about when talking to you. Generation 0 = your generation, -1 = parents, -2 = grandparents.
            </p>
          </div>
          <button
            type="button"
            className="btn btn-ghost text-xs"
            onClick={() =>
              setForm((f: any) => ({
                ...f,
                family_tree: [
                  ...((f as any).family_tree || []),
                  { name: "", relation: "sister", generation: 0, estranged: false, notes: "" },
                ],
              }))
            }
          >
            + Member
          </button>
        </div>
        {((form as any).family_tree || []).map((m: any, i: number) => (
          <div key={i} className="grid gap-2 border border-slate-800 rounded-lg p-3">
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
              <input className={inputClass} placeholder="Name *" value={m.name} onChange={(e) => {
                const next = [...((form as any).family_tree || [])];
                next[i] = { ...next[i], name: e.target.value };
                setForm((f: any) => ({ ...f, family_tree: next }));
              }} />
              <input className={inputClass} placeholder="Relation *" value={m.relation} onChange={(e) => {
                const next = [...((form as any).family_tree || [])];
                next[i] = { ...next[i], relation: e.target.value };
                setForm((f: any) => ({ ...f, family_tree: next }));
              }} />
              <input className={inputClass} type="number" placeholder="Generation" value={m.generation ?? ""} onChange={(e) => {
                const next = [...((form as any).family_tree || [])];
                next[i] = { ...next[i], generation: e.target.value === "" ? null : parseInt(e.target.value, 10) };
                setForm((f: any) => ({ ...f, family_tree: next }));
              }} />
              <label className="text-xs flex items-center gap-1">
                <input type="checkbox" checked={!!m.estranged} onChange={(e) => {
                  const next = [...((form as any).family_tree || [])];
                  next[i] = { ...next[i], estranged: e.target.checked };
                  setForm((f: any) => ({ ...f, family_tree: next }));
                }} /> Estranged
              </label>
            </div>
            <div className="flex gap-2">
              <input className={`${inputClass} flex-1`} placeholder="Notes" value={m.notes || ""} onChange={(e) => {
                const next = [...((form as any).family_tree || [])];
                next[i] = { ...next[i], notes: e.target.value };
                setForm((f: any) => ({ ...f, family_tree: next }));
              }} />
              <button type="button" className="text-xs text-red-400" onClick={() => {
                setForm((f: any) => ({
                  ...f,
                  family_tree: ((f as any).family_tree || []).filter((_: any, j: number) => j !== i),
                }));
              }}>Remove</button>
            </div>
          </div>
        ))}
      </section>

      
      <section className="bg-surface-900 border border-slate-800 rounded-xl p-6 space-y-4">
        <h2 className="font-medium text-slate-200">Persona modes / outfits</h2>
        <p className="text-xs text-slate-500">
          Alternate status mid-story (e.g. “work clothes”, “injured”, or an age for a time-skip).
          Stored on the persona; switch via chat options later or note in custom instructions.
        </p>
        <button
          type="button"
          className="btn btn-ghost text-xs"
          onClick={() =>
            setForm((f: any) => ({
              ...f,
              modes: [...(f.modes || []), { name: "", description: "", age_override: "" }],
            }))
          }
        >
          + Mode
        </button>
        {((form as any).modes || []).map((m: any, i: number) => (
          <div key={i} className="grid gap-2 border border-slate-800 rounded-lg p-3">
            <input className={inputClass} placeholder="Mode name" value={m.name} onChange={(e) => {
              const next = [...((form as any).modes || [])];
              next[i] = { ...next[i], name: e.target.value };
              setForm((f: any) => ({ ...f, modes: next }));
            }} />
            <input className={inputClass} placeholder="Age override (optional)" value={m.age_override || ""} onChange={(e) => {
              const next = [...((form as any).modes || [])];
              next[i] = { ...next[i], age_override: e.target.value };
              setForm((f: any) => ({ ...f, modes: next }));
            }} />
            <textarea className={`${inputClass} min-h-[48px]`} placeholder="Description" value={m.description || ""} onChange={(e) => {
              const next = [...((form as any).modes || [])];
              next[i] = { ...next[i], description: e.target.value };
              setForm((f: any) => ({ ...f, modes: next }));
            }} />
          </div>
        ))}
      </section>

      <div className="flex justify-end gap-3 pb-8">
        <button
          type="button"
          onClick={() => navigate("/personas")}
          className="px-4 py-2 rounded-md text-sm text-slate-300 hover:bg-surface-800"
        >
          Cancel
        </button>
        <button
          type="button"
          disabled={busy}
          onClick={save}
          className="px-5 py-2 rounded-md bg-accent hover:bg-accent-hover text-sm font-medium disabled:opacity-50"
        >
          {busy ? "Saving…" : "Save Persona"}
        </button>
      </div>
    </div>
  );
}
