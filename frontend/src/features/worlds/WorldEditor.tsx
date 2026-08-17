import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { api } from "../../api/client";
import { FormField, inputClass } from "../../components/FormField";

type Loc = { name: string; description: string };
type Faction = { name: string; description: string };
type Obj = { name: string; description: string };

export default function WorldEditor() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [form, setForm] = useState({
    name: "",
    description: "",
    rules: "",
    lore: "",
  });
  const [locations, setLocations] = useState<Loc[]>([]);
  const [factions, setFactions] = useState<Faction[]>([]);
  const [objects, setObjects] = useState<Obj[]>([]);
  const [tagsInput, setTagsInput] = useState("");
  const [tone, setTone] = useState("neutral");
  const [era, setEra] = useState("");
  const [tech, setTech] = useState("");
  const [magic, setMagic] = useState("");
  const [busy, setBusy] = useState(false);
  const [msg, setMsg] = useState<string | null>(null);

  useEffect(() => {
    if (!id) return;
    api.get<any>(`/worlds/${id}`).then((w) => {
      setForm({
        name: w.name || "",
        description: w.description || "",
        rules: w.rules || "",
        lore: w.lore || "",
      });
      setLocations(Array.isArray(w.locations) ? w.locations : []);
      setFactions(Array.isArray(w.factions) ? w.factions : []);
      setObjects(Array.isArray(w.objects) ? w.objects : []);
      setTagsInput((w.tags || []).join(", "));
      // recover optional meta from lore header if stored as JSON in objects later
    });
  }, [id]);

  function updateList<T extends { name: string; description: string }>(
    list: T[],
    setList: (v: T[]) => void,
    index: number,
    key: keyof T,
    value: string
  ) {
    const next = list.map((item, i) =>
      i === index ? { ...item, [key]: value } : item
    );
    setList(next);
  }

  async function save() {
    if (!id) return;
    setBusy(true);
    setMsg(null);
    try {
      const tags = tagsInput
        .split(",")
        .map((t) => t.trim())
        .filter(Boolean);
      // Fold tone/era into rules prefix for prompt without schema change
      const metaLines = [
        tone && tone !== "neutral" ? `Tone: ${tone}` : "",
        era ? `Era: ${era}` : "",
        tech ? `Technology: ${tech}` : "",
        magic ? `Magic / supernatural: ${magic}` : "",
      ].filter(Boolean);
      let rules = form.rules || "";
      if (metaLines.length) {
        const block = metaLines.join("\n");
        rules = rules.includes("Tone:") || rules.includes("Era:")
          ? rules
          : `${block}\n\n${rules}`.trim();
      }
      await api.patch(`/worlds/${id}`, {
        ...form,
        rules,
        locations,
        factions,
        objects,
        tags,
      });
      setMsg("World saved.");
      navigate("/worlds");
    } catch (e) {
      setMsg(String(e));
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="max-w-3xl space-y-6">
      <div className="flex items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">Edit World</h1>
          <p className="text-sm text-slate-400 mt-1">
            Lore and constraints the AI should stay consistent with.
          </p>
        </div>
        <button type="button" className="btn btn-ghost text-sm" onClick={() => navigate("/worlds")}>
          Back
        </button>
      </div>

      {msg && (
        <div className="text-sm text-slate-300 border border-slate-700 rounded-lg px-3 py-2">
          {msg}
        </div>
      )}

      <section className="card p-6 space-y-4">
        <h2 className="font-medium">Basics</h2>
        <FormField label="Name" required>
          <input
            className={inputClass}
            value={form.name}
            onChange={(e) => setForm({ ...form, name: e.target.value })}
          />
        </FormField>
        <FormField label="Description" description="Elevator pitch for this setting.">
          <textarea
            className={`${inputClass} min-h-[100px]`}
            value={form.description}
            onChange={(e) => setForm({ ...form, description: e.target.value })}
          />
        </FormField>
        <FormField label="Tags" description="Comma-separated, e.g. fantasy, noir, school">
          <input
            className={inputClass}
            value={tagsInput}
            onChange={(e) => setTagsInput(e.target.value)}
          />
        </FormField>
      </section>

      <section className="card p-6 space-y-4">
        <h2 className="font-medium">Atmosphere</h2>
        <div className="grid grid-cols-2 gap-3">
          <FormField label="Tone"
            description="Overall emotional color of the setting."
            example="grim"
            hint="Affects how the model narrates tension and hope">
            <select
              className={inputClass}
              value={tone}
              onChange={(e) => setTone(e.target.value)}
            >
              <option value="neutral">Neutral</option>
              <option value="hopeful">Hopeful</option>
              <option value="grim">Grim</option>
              <option value="whimsical">Whimsical</option>
              <option value="romantic">Romantic</option>
              <option value="horror">Horror</option>
              <option value="political">Political intrigue</option>
            </select>
          </FormField>
          <FormField label="Era"
            description="Time period or age of the world."
            example="late industrial / far future"
            hint="Optional">
            <input
              className={inputClass}
              placeholder="e.g. late industrial, far future"
              value={era}
              onChange={(e) => setEra(e.target.value)}
            />
          </FormField>
          <FormField label="Technology level"
            description="What tools and weapons exist."
            example="smartphones + mechs"
            hint="Optional">
            <input
              className={inputClass}
              placeholder="e.g. swords, mechs, smartphones"
              value={tech}
              onChange={(e) => setTech(e.target.value)}
            />
          </FormField>
          <FormField label="Magic / supernatural"
            description="How common the impossible is."
            example="rare blood magic, widely feared"
            hint="Optional">
            <input
              className={inputClass}
              placeholder="e.g. rare blood magic, none"
              value={magic}
              onChange={(e) => setMagic(e.target.value)}
            />
          </FormField>
        </div>
      </section>

      <section className="card p-6 space-y-4">
        <h2 className="font-medium">Rules</h2>
        <p className="text-xs text-slate-500 -mt-2">
          Hard constraints. The model is instructed not to break these.
        </p>
        <textarea
          className={`${inputClass} min-h-[120px]`}
          value={form.rules}
          onChange={(e) => setForm({ ...form, rules: e.target.value })}
          placeholder={"- No firearms\n- Night lasts three days each cycle"}
        />
      </section>

      <section className="card p-6 space-y-4">
        <h2 className="font-medium">Lore</h2>
        <textarea
          className={`${inputClass} min-h-[140px]`}
          value={form.lore}
          onChange={(e) => setForm({ ...form, lore: e.target.value })}
          placeholder="History, myths, current conflicts…"
        />
      </section>

      <section className="card p-6 space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="font-medium">Locations</h2>
          <button
            type="button"
            className="btn btn-ghost text-xs"
            onClick={() => setLocations([...locations, { name: "", description: "" }])}
          >
            + Location
          </button>
        </div>
        {locations.length === 0 && (
          <p className="text-xs text-slate-500">No locations yet.</p>
        )}
        {locations.map((loc, i) => (
          <div key={i} className="grid gap-2 sm:grid-cols-[1fr_2fr_auto] items-start">
            <input
              className={inputClass}
              placeholder="Name"
              value={loc.name}
              onChange={(e) =>
                updateList(locations, setLocations, i, "name", e.target.value)
              }
            />
            <input
              className={inputClass}
              placeholder="Description"
              value={loc.description}
              onChange={(e) =>
                updateList(locations, setLocations, i, "description", e.target.value)
              }
            />
            <button
              type="button"
              className="text-xs text-red-400 px-2 py-2"
              onClick={() => setLocations(locations.filter((_, j) => j !== i))}
            >
              Remove
            </button>
          </div>
        ))}
      </section>

      <section className="card p-6 space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="font-medium">Factions</h2>
          <button
            type="button"
            className="btn btn-ghost text-xs"
            onClick={() => setFactions([...factions, { name: "", description: "" }])}
          >
            + Faction
          </button>
        </div>
        {factions.map((f, i) => (
          <div key={i} className="grid gap-2 sm:grid-cols-[1fr_2fr_auto] items-start">
            <input
              className={inputClass}
              placeholder="Name"
              value={f.name}
              onChange={(e) =>
                updateList(factions, setFactions, i, "name", e.target.value)
              }
            />
            <input
              className={inputClass}
              placeholder="Description"
              value={f.description}
              onChange={(e) =>
                updateList(factions, setFactions, i, "description", e.target.value)
              }
            />
            <button
              type="button"
              className="text-xs text-red-400 px-2 py-2"
              onClick={() => setFactions(factions.filter((_, j) => j !== i))}
            >
              Remove
            </button>
          </div>
        ))}
      </section>

      <section className="card p-6 space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="font-medium">Notable objects / artifacts</h2>
          <button
            type="button"
            className="btn btn-ghost text-xs"
            onClick={() => setObjects([...objects, { name: "", description: "" }])}
          >
            + Object
          </button>
        </div>
        {objects.map((o, i) => (
          <div key={i} className="grid gap-2 sm:grid-cols-[1fr_2fr_auto] items-start">
            <input
              className={inputClass}
              placeholder="Name"
              value={o.name}
              onChange={(e) =>
                updateList(objects, setObjects, i, "name", e.target.value)
              }
            />
            <input
              className={inputClass}
              placeholder="Description"
              value={o.description}
              onChange={(e) =>
                updateList(objects, setObjects, i, "description", e.target.value)
              }
            />
            <button
              type="button"
              className="text-xs text-red-400 px-2 py-2"
              onClick={() => setObjects(objects.filter((_, j) => j !== i))}
            >
              Remove
            </button>
          </div>
        ))}
      </section>

      <div className="flex gap-2 justify-end pb-8">
        <button type="button" className="btn btn-ghost" onClick={() => navigate("/worlds")}>
          Cancel
        </button>
        <button type="button" className="btn btn-primary" disabled={busy} onClick={save}>
          {busy ? "Saving…" : "Save world"}
        </button>
      </div>
    </div>
  );
}
