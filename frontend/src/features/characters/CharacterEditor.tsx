import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { charactersApi } from "../../api/characters";
import type { Character } from "../../types";
import { FormField, inputClass } from "../../components/FormField";

const empty: Partial<Character> = {
  name: "",
  description: "",
  filter_level: "mature",
  system_prompt: "",
  baseline_personality: "",
  scenario: "",
  greeting: "",
  temperature: 0.85,
  top_p: 0.9,
  repetition_penalty: 1.1,
  context_window: 4096,
  max_tokens: 512,
  side_character_enabled: true,
  side_character_instructions: "",
  tags: [],
  example_dialogues: [],
  traits: [],
  likes: [],
  dislikes: [],
  habits: [],
  additional_facts: [],
  family_tree: [],
  relationships: [],
  image_gen_enabled: false,
};

export default function CharacterEditor() {
  const { id } = useParams();
  const isNew = !id || id === "new";
  const navigate = useNavigate();
  const [form, setForm] = useState<Partial<Character>>(empty);
  const [tagsInput, setTagsInput] = useState("");
  const [factsInput, setFactsInput] = useState("");
  const [likesInput, setLikesInput] = useState("");
  const [dislikesInput, setDislikesInput] = useState("");
  const [traitsInput, setTraitsInput] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!isNew && id) {
      charactersApi
        .get(id)
        .then((c) => {
          setForm(c);
          setTagsInput((c.tags || []).join(", "));
          setFactsInput((c.additional_facts || []).join("\n"));
          setLikesInput((c.likes || []).join(", "));
          setDislikesInput((c.dislikes || []).join(", "));
          setTraitsInput((c.traits || []).join(", "));
        })
        .catch((e) => setError(String(e)));
    }
  }, [id, isNew]);

  function update<K extends keyof Character>(key: K, value: Character[K]) {
    setForm((f) => ({ ...f, [key]: value }));
  }

  async function save() {
    if (!form.name?.trim()) {
      setError("Name is required");
      return;
    }
    setBusy(true);
    setError(null);
    const payload = {
      ...form,
      tags: tagsInput.split(",").map((t) => t.trim()).filter(Boolean),
      additional_facts: factsInput.split("\n").map((t) => t.trim()).filter(Boolean),
      likes: likesInput.split(",").map((t) => t.trim()).filter(Boolean),
      dislikes: dislikesInput.split(",").map((t) => t.trim()).filter(Boolean),
      traits: traitsInput.split(",").map((t) => t.trim()).filter(Boolean),
    };
    try {
      if (isNew) {
        const created = await charactersApi.create(payload);
        navigate(`/characters/${created.id}`);
      } else {
        await charactersApi.update(id!, payload);
        navigate(`/characters/${id}`);
      }
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
            {isNew ? "New Character" : "Edit Character"}
          </h1>
          <p className="text-sm text-slate-400 mt-1">
            Characters define who the AI is — personality, scenario, greeting,
            and generation defaults.
          </p>
          <p className="text-xs text-amber-400/90 mt-2">
            Required: Name. Recommended: system prompt or personality, greeting, filter level.
            Use {"{{user}}"} / {"{{char}}"} in prompts.
          </p>
        </div>
        <button
          type="button"
          onClick={() => navigate("/characters")}
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

        <FormField
          label="Name"
          required
          description="The display name of this character. Shown in the browser and in chat headers."
          example="Alice"
        >
          <input
            className={inputClass}
            value={form.name || ""}
            onChange={(e) => update("name", e.target.value)}
            placeholder="Alice"
          />
        </FormField>

        <FormField
          label="Description"
          description="A short summary shown on the character card in the browser. Not sent to the model."
          example="A friendly tavern keeper who knows every rumor in town."
        >
          <textarea
            className={`${inputClass} min-h-[72px]`}
            value={form.description || ""}
            onChange={(e) => update("description", e.target.value)}
            placeholder="A friendly tavern keeper who knows every rumor in town."
          />
        </FormField>

        <FormField
          label="Tags"
          description="Comma-separated labels for filtering and organisation."
          example="fantasy, tavern, friendly"
        >
          <input
            className={inputClass}
            value={tagsInput}
            onChange={(e) => setTagsInput(e.target.value)}
            placeholder="fantasy, tavern, friendly"
          />
        </FormField>
      </section>

      {/* Prompt material */}
      <section className="bg-surface-900 border border-slate-800 rounded-xl p-6 space-y-5">
        <h2 className="font-medium text-slate-200">Prompt Material</h2>
        <p className="text-xs text-slate-500 -mt-2">
          These fields are compiled into the system prompt sent to the local
          model. Use {"{{user}}"} for the active persona name.
        </p>
        <div className="flex flex-wrap gap-2">
          <button
            type="button"
            className="btn btn-ghost text-xs"
            onClick={() =>
              update(
                "system_prompt",
                (form.system_prompt || "") +
                  "\nYou are speaking with {{user}}. Use their persona facts when asked about their life or family."
              )
            }
          >
            Add persona-awareness line
          </button>
          <button
            type="button"
            className="btn btn-ghost text-xs"
            onClick={() =>
              update(
                "system_prompt",
                (form.system_prompt || "") +
                  "\nStay in first person. Never narrate yourself in third person."
              )
            }
          >
            Force first-person
          </button>
          <button
            type="button"
            className="btn btn-ghost text-xs"
            onClick={() =>
              update(
                "greeting",
                form.greeting || '— "Hey, {{user}}. Didn\'t expect to see you here."'
              )
            }
          >
            Sample greeting
          </button>
        </div>

        <FormField
          label="System Prompt"
          description="Core instructions that define how the AI behaves. Highest priority guidance."
          example='You are Alice, a warm tavern keeper in the port city of Eldoria. Stay in character at all times.'
        >
          <textarea
            className={`${inputClass} min-h-[100px] font-mono text-sm`}
            value={form.system_prompt || ""}
            onChange={(e) => update("system_prompt", e.target.value)}
            placeholder="You are Alice, a warm tavern keeper…"
          />
        </FormField>

        <FormField
          label="Baseline Personality"
          description="Traits, mannerisms, and emotional tone that should always come through."
          example="Warm, slightly sarcastic, protective of regulars, loves gossip."
        >
          <textarea
            className={`${inputClass} min-h-[80px]`}
            value={form.baseline_personality || ""}
            onChange={(e) => update("baseline_personality", e.target.value)}
            placeholder="Warm, slightly sarcastic, protective of regulars…"
          />
        </FormField>

        <FormField
          label="Scenario"
          description="The starting situation or setting for new conversations with this character."
          example="You are sitting at the bar of The Silver Anchor on a rainy evening."
        >
          <textarea
            className={`${inputClass} min-h-[80px]`}
            value={form.scenario || ""}
            onChange={(e) => update("scenario", e.target.value)}
            placeholder="You are sitting at the bar of The Silver Anchor…"
          />
        </FormField>

        <FormField
          label="Greeting"
          description="The first message the character sends when a new chat starts. Use the roleplay markup (— for dialogue, * for actions)."
          example={'— "Evening, stranger. What can I get you?"'}
        >
          <textarea
            className={`${inputClass} min-h-[220px] font-mono text-sm`}
            value={form.greeting || ""}
            onChange={(e) => update("greeting", e.target.value)}
            placeholder={'— "Evening, stranger. What can I get you?"'}
          />
        </FormField>
      </section>

      {/* Generation defaults */}
      <section className="bg-surface-900 border border-slate-800 rounded-xl p-6 space-y-5">
        <h2 className="font-medium text-slate-200">Generation Defaults</h2>
        <p className="text-xs text-slate-500 -mt-2">
          These apply when a chat uses this character unless overridden per
          message. Leave blank to use the application default.
        </p>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-5">
          <FormField
            label="Temperature"
          description="Randomness of replies."
          hint="Min 0 · Max 2 · Default 0.85"
          example="0.85"
            description="Controls randomness. Lower = more focused and predictable; higher = more creative and varied."
            hint="Min 0.0 · Max 2.0 · Default 0.85"
            example="0.85"
          >
            <input
              type="number"
              step="0.05"
              min={0}
              max={2}
              className={inputClass}
              value={form.temperature ?? 0.85}
              onChange={(e) =>
                update("temperature", parseFloat(e.target.value) || 0)
              }
            />
          </FormField>

          <FormField
            label="Top P"
            description="Nucleus sampling threshold. Limits the token pool to the most likely cumulative probability mass."
            hint="Min 0.0 · Max 1.0 · Default 0.9"
            example="0.9"
          >
            <input
              type="number"
              step="0.05"
              min={0}
              max={1}
              className={inputClass}
              value={form.top_p ?? 0.9}
              onChange={(e) =>
                update("top_p", parseFloat(e.target.value) || 0)
              }
            />
          </FormField>

          <FormField
            label="Repetition Penalty"
            description="Discourages the model from repeating the same phrases. 1.0 = no penalty."
            hint="Min 0.5 · Max 2.0 · Default 1.1"
            example="1.1"
          >
            <input
              type="number"
              step="0.05"
              min={0.5}
              max={2}
              className={inputClass}
              value={form.repetition_penalty ?? 1.1}
              onChange={(e) =>
                update(
                  "repetition_penalty",
                  parseFloat(e.target.value) || 1
                )
              }
            />
          </FormField>

          <FormField
            label="Max Tokens"
            description="Maximum number of tokens the model may generate in a single response. Higher values allow longer replies but use more context and time."
            hint="Min 16 · Max 8192 · Default 512"
            example="512"
          >
            <input
              type="number"
              min={16}
              max={8192}
              step={16}
              className={inputClass}
              value={form.max_tokens ?? 512}
              onChange={(e) =>
                update("max_tokens", parseInt(e.target.value, 10) || 512)
              }
            />
          </FormField>

          <FormField
            label="Context Window"
            description="How many tokens of conversation history the model can see. Must fit within the loaded model’s context size."
            hint="Min 512 · Max 131072 · Default 4096"
            example="4096"
          >
            <input
              type="number"
              min={512}
              max={131072}
              step={256}
              className={inputClass}
              value={form.context_window ?? 4096}
              onChange={(e) =>
                update(
                  "context_window",
                  parseInt(e.target.value, 10) || 4096
                )
              }
            />
          </FormField>

          <FormField
            label="Model Name (optional)"
            description="Override the application default model for this character only. Leave empty to use the global default."
            example="llama3.2:3b"
          >
            <input
              className={inputClass}
              value={form.model_name || ""}
              onChange={(e) => update("model_name", e.target.value || null)}
              placeholder="(use application default)"
            />
          </FormField>
        </div>

        <label className="flex items-start gap-2 text-sm pt-1">
          <input
            type="checkbox"
            className="mt-1"
            checked={form.side_character_enabled ?? true}
            onChange={(e) =>
              update("side_character_enabled", e.target.checked)
            }
          />
          <span>
            <span className="font-medium text-slate-200">
              Enable side characters
            </span>
            <span className="block text-xs text-slate-400 mt-0.5">
              Allow this character to introduce and control other speakers
              (waiter, passer-by, etc.) as separate message bubbles.
            </span>
          </span>
        </label>

        <FormField
          label="Side-character instructions"
          description="Extra guidance for how and when side characters may appear."
          example="Only introduce side characters when the scene naturally calls for them. Keep their dialogue brief."
        >
          <textarea
            className={`${inputClass} min-h-[72px]`}
            value={form.side_character_instructions || ""}
            onChange={(e) =>
              update("side_character_instructions", e.target.value)
            }
            placeholder="Only introduce side characters when the scene naturally calls for them…"
          />
        </FormField>
      </section>


      {/* Content filter */}
      <section className="bg-surface-900 border border-slate-800 rounded-xl p-6 space-y-4">
        <h2 className="font-medium text-slate-200">Content filter</h2>
        <p className="text-xs text-slate-500">How explicit this character may be in roleplay.</p>
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
          {(["strict", "moderate", "mature", "unfiltered"] as const).map((lvl) => (
            <button
              key={lvl}
              type="button"
              onClick={() => update("filter_level", lvl)}
              className={`px-2 py-2 rounded-lg border text-sm capitalize ${
                (form.filter_level || "mature") === lvl
                  ? "border-accent bg-accent/15"
                  : "border-slate-700"
              }`}
            >
              {lvl}
            </button>
          ))}
        </div>
      </section>

      {/* Appearance & deep profile */}
      <section className="bg-surface-900 border border-slate-800 rounded-xl p-6 space-y-4">
        <h2 className="font-medium text-slate-200">Appearance & identity details</h2>
        <p className="text-xs text-slate-500 -mt-2">
          Optional but recommended. The model uses these when describing you-as-the-character and when others react to you.
        </p>
        <div className="grid grid-cols-2 gap-3">
          <FormField label="Age" description="Number or range." example="19" hint="Optional">
            <input className={inputClass} value={form.age || ""} onChange={(e) => update("age", e.target.value)} placeholder="19" />
          </FormField>
          <FormField label="Pronouns" description="How the character is referred to." example="she/her" hint="Optional">
            <input className={inputClass} value={form.pronouns || ""} onChange={(e) => update("pronouns", e.target.value)} placeholder="she/her" />
          </FormField>
          <FormField label="Height" description="Relative or exact." example="165 cm / 5'5&quot;" hint="Optional">
            <input className={inputClass} value={form.height || ""} onChange={(e) => update("height", e.target.value)} placeholder="165 cm" />
          </FormField>
          <FormField label="Build" description="Body type at a glance." example="slim, athletic" hint="Optional">
            <input className={inputClass} value={form.build || ""} onChange={(e) => update("build", e.target.value)} placeholder="slim" />
          </FormField>
          <FormField label="Hair" description="Color, length, style." example="long black hair, usually in a braid" hint="Optional">
            <input className={inputClass} value={form.hair || ""} onChange={(e) => update("hair", e.target.value)} />
          </FormField>
          <FormField label="Eyes" description="Color and expression." example="sharp blue eyes" hint="Optional">
            <input className={inputClass} value={form.eyes || ""} onChange={(e) => update("eyes", e.target.value)} />
          </FormField>
          <FormField label="Skin" description="Tone or notable marks." example="fair, faint scar on left brow" hint="Optional">
            <input className={inputClass} value={form.skin || ""} onChange={(e) => update("skin", e.target.value)} />
          </FormField>
          <FormField label="Clothing" description="Default outfit or style." example="school uniform, loose coat" hint="Optional">
            <input className={inputClass} value={form.clothing || ""} onChange={(e) => update("clothing", e.target.value)} />
          </FormField>
        </div>
        <FormField
          label="Appearance description"
          description="Free-form look. Overrides the short fields when present."
          example="A tall young woman with tired eyes and ink-stained fingers."
          hint="Optional · max ~4000 chars"
        >
          <textarea className={`${inputClass} min-h-[80px]`} value={form.appearance_description || ""} onChange={(e) => update("appearance_description", e.target.value)} />
        </FormField>
        <FormField label="Traits" description="Personality keywords, comma-separated." example="proud, loyal, sharp-tongued" hint="Optional">
          <input className={inputClass} value={traitsInput} onChange={(e) => setTraitsInput(e.target.value)} />
        </FormField>
        <FormField label="Likes" description="Comma-separated." example="tea, quiet libraries, honesty" hint="Optional">
          <input className={inputClass} value={likesInput} onChange={(e) => setLikesInput(e.target.value)} />
        </FormField>
        <FormField label="Dislikes" description="Comma-separated." example="liars, crowds, being underestimated" hint="Optional">
          <input className={inputClass} value={dislikesInput} onChange={(e) => setDislikesInput(e.target.value)} />
        </FormField>
        <FormField label="Speaking style" description="How dialogue should sound." example="curt, formal, dry humor" hint="Optional">
          <input className={inputClass} value={form.speaking_style || ""} onChange={(e) => update("speaking_style", e.target.value)} />
        </FormField>
        <FormField label="Occupation" description="Job or role in the setting." example="student council vice-president" hint="Optional">
          <input className={inputClass} value={form.occupation || ""} onChange={(e) => update("occupation", e.target.value)} />
        </FormField>
        <FormField label="Location" description="Where they usually are." example="Kamiyama High, Tokyo" hint="Optional">
          <input className={inputClass} value={form.location || ""} onChange={(e) => update("location", e.target.value)} />
        </FormField>
        <FormField label="Biography" description="Backstory the model should know." example="Grew up overseas; returned two years ago." hint="Optional">
          <textarea className={`${inputClass} min-h-[100px]`} value={form.biography || ""} onChange={(e) => update("biography", e.target.value)} />
        </FormField>
        <FormField label="Goals" description="What they want." example="Protect her reputation; graduate early." hint="Optional">
          <textarea className={`${inputClass} min-h-[60px]`} value={form.goals || ""} onChange={(e) => update("goals", e.target.value)} />
        </FormField>
        <FormField label="Fears" description="What unsettles them." example="Being abandoned; public failure." hint="Optional">
          <textarea className={`${inputClass} min-h-[60px]`} value={form.fears || ""} onChange={(e) => update("fears", e.target.value)} />
        </FormField>
        <FormField label="Secrets" description="Model knows these; will not volunteer them unless the scene forces it." example="She still writes letters she never sends." hint="Optional">
          <textarea className={`${inputClass} min-h-[60px]`} value={form.secrets || ""} onChange={(e) => update("secrets", e.target.value)} />
        </FormField>
        <FormField label="Additional facts" description="One fact per line (family, history, quirks)." example="Has a younger brother named Ken" hint="Optional">
          <textarea className={`${inputClass} min-h-[80px]`} value={factsInput} onChange={(e) => setFactsInput(e.target.value)} />
        </FormField>
        <FormField label="How they act" description="Default body language and energy." example="Stands straight; fidgets with sleeves when nervous." hint="Optional">
          <textarea className={`${inputClass} min-h-[60px]`} value={form.how_they_act || ""} onChange={(e) => update("how_they_act", e.target.value)} />
        </FormField>
        <FormField label="How they respond" description="How they answer conflict or affection." example="Deflects with sarcasm, then softens if pressed." hint="Optional">
          <textarea className={`${inputClass} min-h-[60px]`} value={form.how_they_respond || ""} onChange={(e) => update("how_they_respond", e.target.value)} />
        </FormField>
        <FormField label="Custom instructions" description="Hard rules for the model about this character." example="Never break first person. Never mention OOC." hint="Optional">
          <textarea className={`${inputClass} min-h-[60px]`} value={form.custom_instructions || ""} onChange={(e) => update("custom_instructions", e.target.value)} />
        </FormField>
      </section>

      {/* Response length */}
      <section className="bg-surface-900 border border-slate-800 rounded-xl p-6 space-y-4">
        <h2 className="font-medium text-slate-200">Response length</h2>
        <p className="text-xs text-slate-500 -mt-2">
          Controls how long replies tend to be (max tokens). You can still type a custom number below.
        </p>
        <div className="flex flex-wrap gap-2">
          {(
            [
              [128, "Short"],
              [256, "Medium-short"],
              [512, "Medium"],
              [768, "Long"],
              [1024, "Very long"],
            ] as const
          ).map(([n, label]) => (
            <button
              key={n}
              type="button"
              onClick={() => update("max_tokens", n)}
              className={`px-3 py-2 rounded-lg border text-sm ${
                (form.max_tokens ?? 512) === n ? "border-accent bg-accent/15" : "border-slate-700"
              }`}
            >
              {label} ({n})
            </button>
          ))}
        </div>
        <FormField
          label="Max tokens"
          description="Hard upper bound on generated tokens for this character."
          hint="Min 16 · Max 8192 · Default 512"
          example="512"
        >
          <input
            className={inputClass}
            type="number"
            min={16}
            max={8192}
            value={form.max_tokens ?? 512}
            onChange={(e) => update("max_tokens", parseInt(e.target.value, 10) || 512)}
          />
        </FormField>
      </section>

      {/* Family tree */}
      <section className="bg-surface-900 border border-slate-800 rounded-xl p-6 space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="font-medium text-slate-200">Family tree</h2>
            <p className="text-xs text-slate-500">Go back generations; mark estranged relatives.</p>
          </div>
          <button
            type="button"
            className="btn btn-ghost text-xs"
            onClick={() =>
              update("family_tree", [
                ...(form.family_tree || []),
                { name: "", relation: "relative", generation: -1, estranged: false, notes: "" },
              ])
            }
          >
            + Member
          </button>
        </div>
        {(form.family_tree || []).map((m, i) => (
          <div key={i} className="grid gap-2 border border-slate-800 rounded-lg p-3">
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
              <input className={inputClass} placeholder="Name" value={m.name} onChange={(e) => {
                const next = [...(form.family_tree || [])];
                next[i] = { ...next[i], name: e.target.value };
                update("family_tree", next);
              }} />
              <input className={inputClass} placeholder="Relation" value={m.relation} onChange={(e) => {
                const next = [...(form.family_tree || [])];
                next[i] = { ...next[i], relation: e.target.value };
                update("family_tree", next);
              }} />
              <input className={inputClass} type="number" placeholder="Gen (-1 parent)" value={m.generation ?? ""} onChange={(e) => {
                const next = [...(form.family_tree || [])];
                next[i] = { ...next[i], generation: e.target.value === "" ? null : parseInt(e.target.value, 10) };
                update("family_tree", next);
              }} />
              <input className={inputClass} placeholder="Status" value={m.status || ""} onChange={(e) => {
                const next = [...(form.family_tree || [])];
                next[i] = { ...next[i], status: e.target.value };
                update("family_tree", next);
              }} />
            </div>
            <div className="flex gap-3 items-center">
              <label className="text-xs flex items-center gap-1">
                <input type="checkbox" checked={!!m.estranged} onChange={(e) => {
                  const next = [...(form.family_tree || [])];
                  next[i] = { ...next[i], estranged: e.target.checked };
                  update("family_tree", next);
                }} /> Estranged
              </label>
              <input className={`${inputClass} flex-1`} placeholder="Notes" value={m.notes || ""} onChange={(e) => {
                const next = [...(form.family_tree || [])];
                next[i] = { ...next[i], notes: e.target.value };
                update("family_tree", next);
              }} />
              <button type="button" className="text-xs text-red-400" onClick={() => {
                update("family_tree", (form.family_tree || []).filter((_, j) => j !== i));
              }}>Remove</button>
            </div>
          </div>
        ))}
      </section>

      {/* Avatar & optional image gen */}
      <section className="bg-surface-900 border border-slate-800 rounded-xl p-6 space-y-4">
        <h2 className="font-medium text-slate-200">Avatar & image generation</h2>
        {form.avatar_path && (
          <img src={form.avatar_path} alt="" className="w-24 h-24 rounded-xl object-cover border border-slate-700" />
        )}
        {!isNew && id && (
          <input
            type="file"
            accept="image/*"
            onChange={async (e) => {
              const file = e.target.files?.[0];
              if (!file) return;
              const fd = new FormData();
              fd.append("file", file);
              const res = await fetch(`/api/images/characters/${id}/avatar`, { method: "POST", body: fd });
              if (res.ok) {
                const data = await res.json();
                update("avatar_path", data.avatar_path);
              } else {
                setError(await res.text());
              }
            }}
          />
        )}
        {isNew && <p className="text-xs text-slate-500">Save the character first, then upload an avatar.</p>}
        <label className="flex items-center gap-2 text-sm">
          <input
            type="checkbox"
            checked={!!form.image_gen_enabled}
            onChange={(e) => update("image_gen_enabled", e.target.checked)}
          />
          Allow optional local image generation for this character
        </label>
        <FormField label="Image style prompt" description="Appended when generating images via local SD (not required).">
          <textarea className={`${inputClass} min-h-[60px]`} value={form.image_gen_style || ""} onChange={(e) => update("image_gen_style", e.target.value)} placeholder="anime style, soft lighting…" />
        </FormField>
      </section>



      <section className="bg-surface-900 border border-slate-800 rounded-xl p-6 space-y-4">
        <h2 className="font-medium text-slate-200">Side roster & triggers</h2>
        <p className="text-xs text-slate-500">
          Named NPCs you can summon with /as Name line. Trigger phrases bias reactions when the user says something matching.
        </p>
        <button
          type="button"
          className="btn btn-ghost text-xs"
          onClick={() =>
            update("side_roster", [
              ...((form.side_roster as any) || []),
              { name: "", notes: "" },
            ] as any)
          }
        >
          + NPC
        </button>
        {((form.side_roster as any) || []).map((n: any, i: number) => (
          <div key={i} className="flex gap-2">
            <input
              className={inputClass}
              placeholder="Name"
              value={n.name}
              onChange={(e) => {
                const next = [...((form.side_roster as any) || [])];
                next[i] = { ...next[i], name: e.target.value };
                update("side_roster", next as any);
              }}
            />
            <input
              className={inputClass}
              placeholder="Notes"
              value={n.notes || ""}
              onChange={(e) => {
                const next = [...((form.side_roster as any) || [])];
                next[i] = { ...next[i], notes: e.target.value };
                update("side_roster", next as any);
              }}
            />
            <button
              type="button"
              className="text-xs text-red-400"
              onClick={() =>
                update(
                  "side_roster",
                  ((form.side_roster as any) || []).filter((_: any, j: number) => j !== i) as any
                )
              }
            >
              ×
            </button>
          </div>
        ))}
        <button
          type="button"
          className="btn btn-ghost text-xs"
          onClick={() =>
            update("trigger_phrases", [
              ...((form.trigger_phrases as any) || []),
              { phrase: "", reaction: "" },
            ] as any)
          }
        >
          + Trigger
        </button>
        {((form.trigger_phrases as any) || []).map((tr: any, i: number) => (
          <div key={i} className="flex gap-2">
            <input
              className={inputClass}
              placeholder="If user mentions…"
              value={tr.phrase}
              onChange={(e) => {
                const next = [...((form.trigger_phrases as any) || [])];
                next[i] = { ...next[i], phrase: e.target.value };
                update("trigger_phrases", next as any);
              }}
            />
            <input
              className={inputClass}
              placeholder="Bias toward…"
              value={tr.reaction}
              onChange={(e) => {
                const next = [...((form.trigger_phrases as any) || [])];
                next[i] = { ...next[i], reaction: e.target.value };
                update("trigger_phrases", next as any);
              }}
            />
            <button
              type="button"
              className="text-xs text-red-400"
              onClick={() =>
                update(
                  "trigger_phrases",
                  ((form.trigger_phrases as any) || []).filter((_: any, j: number) => j !== i) as any
                )
              }
            >
              ×
            </button>
          </div>
        ))}
        <FormField
          label="Mood board paths"
          description="Local image URLs or /api/images/media/… paths, one per line. Visual reference only."
          example="/api/images/media/avatar_….png"
        >
          <textarea
            className={`${inputClass} min-h-[60px] font-mono text-xs`}
            value={((form.mood_board as any) || []).join("\n")}
            onChange={(e) =>
              update(
                "mood_board",
                e.target.value.split("\n").map((s) => s.trim()).filter(Boolean) as any
              )
            }
          />
        </FormField>
      </section>

      <div className="flex justify-end gap-3 pb-8">
        <button
          type="button"
          onClick={() => navigate("/characters")}
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
          {busy ? "Saving…" : "Save Character"}
        </button>
      </div>
    </div>
  );
}
