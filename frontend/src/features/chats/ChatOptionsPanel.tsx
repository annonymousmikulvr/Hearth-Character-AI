import { useEffect, useRef, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../../api/client";
import { conversationsApi } from "../../api/conversations";
import { useAppStore } from "../../stores/appStore";
import { useUiPackStore } from "../../stores/uiPackStore";
import type { Conversation } from "../../types";

type Tab =
  | "history"
  | "memory"
  | "filter"
  | "layout"
  | "wallpaper"
  | "style"
  | "persona"
  | "intensity"
  | "branches";

interface Props {
  conversation: Conversation;
  onConversationUpdate: (c: Conversation) => void;
}

export default function ChatOptionsPanel({
  conversation,
  onConversationUpdate,
}: Props) {
  const [open, setOpen] = useState(false);
  const [tab, setTab] = useState<Tab>("history");
  const panelRef = useRef<HTMLDivElement>(null);
  const { personas, loadPersonas } = useAppStore();
  const {
    chatLayout,
    setChatLayout,
    chatWallpaper,
    setChatWallpaper,
    packs,
    importPack,
    exportActive,
    setActivePack,
    activePackId,
  } = useUiPackStore();

  const [history, setHistory] = useState<
    { id: string; title?: string | null; last_message_at?: string | null }[]
  >([]);
  const [memories, setMemories] = useState<
    { id: string; content: string; owner_type: string }[]
  >([]);
  const [models, setModels] = useState<string[]>([]);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    if (!open) return;
    loadPersonas();
    conversationsApi
      .list({ character_id: conversation.character_id })
      .then((list) => setHistory(list))
      .catch(console.error);
    api
      .get<{ id: string; content: string; owner_type: string; owner_id: string }[]>(
        "/memories?limit=100"
      )
      .then((all) =>
        setMemories(
          all.filter(
            (m) =>
              (m.owner_type === "conversation" &&
                m.owner_id === conversation.id) ||
              (m.owner_type === "character" &&
                m.owner_id === conversation.character_id) ||
              (m.owner_type === "persona" &&
                m.owner_id === conversation.persona_id)
          )
        )
      )
      .catch(console.error);
    api
      .get<{ models: string[] }>("/ai/connection")
      .then((c) => setModels(c.models || []))
      .catch(() => {});
  }, [open, conversation]);

  useEffect(() => {
    function onDoc(e: MouseEvent) {
      if (panelRef.current && !panelRef.current.contains(e.target as Node)) {
        setOpen(false);
      }
    }
    if (open) document.addEventListener("mousedown", onDoc);
    return () => document.removeEventListener("mousedown", onDoc);
  }, [open]);

  async function switchPersona(personaId: string) {
    const p = personas.find((x) => x.id === personaId);
    if (!p) return;
    setBusy(true);
    try {
      const updated = await conversationsApi.update(conversation.id, {
        persona_id: personaId,
        persona_display_name: p.chat_name,
      } as any);
      onConversationUpdate(updated);
    } finally {
      setBusy(false);
    }
  }

  async function setModel(model: string) {
    setBusy(true);
    try {
      const updated = await conversationsApi.update(conversation.id, {
        model_name: model || null,
      } as any);
      onConversationUpdate(updated);
    } finally {
      setBusy(false);
    }
  }

  const tabs: { id: Tab; label: string }[] = [
    { id: "history", label: "History" },
    { id: "memory", label: "Memory" },
    { id: "filter", label: "Filter" },
    { id: "layout", label: "Layout" },
    { id: "wallpaper", label: "Wallpaper" },
    { id: "style", label: "Chat style" },
    { id: "persona", label: "Persona" },
    { id: "intensity", label: "Intensity" },
    { id: "branches", label: "Branches" },
  ];

  return (
    <div className="relative" ref={panelRef}>
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        className="h-11 w-11 rounded-lg border border-slate-700 bg-surface-900 hover:border-accent/50 text-slate-300 flex items-center justify-center shrink-0"
        title="Chat options"
        aria-label="Chat options"
      >
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <circle cx="12" cy="12" r="3" />
          <path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4" />
        </svg>
      </button>

      {open && (
        <div className="absolute bottom-full right-0 mb-2 w-[min(100vw-2rem,22rem)] max-h-[70vh] overflow-hidden rounded-2xl border border-slate-700 bg-surface-900 shadow-2xl z-30 flex flex-col">
          <div className="px-3 py-2 border-b border-slate-800 text-xs font-medium text-slate-400">
            Chat options
          </div>
          <div className="flex flex-wrap gap-1 p-2 border-b border-slate-800">
            {tabs.map((t) => (
              <button
                key={t.id}
                type="button"
                onClick={() => setTab(t.id)}
                className={`text-[11px] px-2 py-1 rounded-md ${
                  tab === t.id
                    ? "bg-accent text-white"
                    : "text-slate-400 hover:bg-surface-800"
                }`}
              >
                {t.label}
              </button>
            ))}
          </div>
          <div className="p-3 overflow-y-auto text-sm space-y-2 min-h-[8rem]">
            {tab === "history" && (
              <>
                <p className="text-xs text-slate-500">
                  Other chats with {conversation.character_name || "this character"}.
                </p>
                {history.map((h) => (
                  <Link
                    key={h.id}
                    to={`/chats/${h.id}`}
                    onClick={() => setOpen(false)}
                    className={`block rounded-lg px-2 py-1.5 hover:bg-surface-800 ${
                      h.id === conversation.id ? "text-accent-muted" : ""
                    }`}
                  >
                    <div className="truncate text-sm">
                      {h.title || "Untitled chat"}
                    </div>
                    <div className="text-[10px] text-slate-500">
                      {h.last_message_at || ""}
                    </div>
                  </Link>
                ))}
                <Link
                  to={`/chats/new?character=${conversation.character_id}`}
                  className="text-xs text-accent-muted block pt-1"
                  onClick={() => setOpen(false)}
                >
                  + New chat with this character
                </Link>
              </>
            )}

            {tab === "memory" && (
              <>
                <p className="text-xs text-slate-500">
                  Facts the model can recall for this chat / character / persona.
                </p>
                {memories.length === 0 && (
                  <p className="text-xs text-slate-500">No memories yet.</p>
                )}
                {memories.map((m) => (
                  <div
                    key={m.id}
                    className="text-xs rounded-lg bg-surface-950 border border-slate-800 px-2 py-1.5"
                  >
                    <span className="text-slate-500">[{m.owner_type}]</span>{" "}
                    {m.content}
                  </div>
                ))}
              </>
            )}

            
            {tab === "filter" && (
              <>
                <p className="text-xs text-slate-500">
                  Content filter for this chat only. Does not change the character card permanently.
                </p>
                {(
                  [
                    ["strict", "Strict — clean language"],
                    ["moderate", "Moderate — mild"],
                    ["mature", "Mature — adult themes"],
                    ["unfiltered", "Unfiltered — adult RP"],
                  ] as const
                ).map(([id, label]) => (
                  <button
                    key={id}
                    type="button"
                    disabled={busy}
                    onClick={async () => {
                      setBusy(true);
                      try {
                        const updated = await conversationsApi.update(conversation.id, {
                          filter_level: id,
                        } as any);
                        onConversationUpdate({ ...conversation, ...updated, filter_level: id });
                      } finally {
                        setBusy(false);
                      }
                    }}
                    className={`w-full text-left px-2 py-1.5 rounded-lg text-sm ${
                      (conversation.filter_level || "mature") === id
                        ? "bg-accent/20 text-accent-muted"
                        : "hover:bg-surface-800"
                    }`}
                  >
                    {label}
                  </button>
                ))}
              </>
            )}

            {tab === "layout" && (
              <>
                <p className="text-xs text-slate-500">
                  How message bubbles are arranged in this browser.
                </p>
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
                    className={`w-full text-left px-2 py-1.5 rounded-lg text-sm ${
                      chatLayout === id
                        ? "bg-accent/20 text-accent-muted"
                        : "hover:bg-surface-800"
                    }`}
                  >
                    {label}
                  </button>
                ))}
              </>
            )}

            {tab === "wallpaper" && (
              <>
                <p className="text-xs text-slate-500">
                  CSS background for the chat area (color, gradient, or image url).
                </p>
                <textarea
                  className="w-full bg-surface-950 border border-slate-700 rounded-lg px-2 py-1.5 text-xs min-h-[72px]"
                  placeholder='e.g. linear-gradient(#0f172a,#1e1b4b) or url("/my.png")'
                  value={chatWallpaper}
                  onChange={(e) => setChatWallpaper(e.target.value)}
                />
                <button
                  type="button"
                  className="text-xs text-slate-400"
                  onClick={() => setChatWallpaper("")}
                >
                  Clear wallpaper
                </button>
                <div className="pt-2 border-t border-slate-800 space-y-1">
                  <p className="text-xs text-slate-500">Custom UI packs</p>
                  {packs.map((p) => (
                    <button
                      key={p.id}
                      type="button"
                      className={`w-full text-left text-xs px-2 py-1 rounded ${
                        activePackId === p.id ? "bg-accent/20" : "hover:bg-surface-800"
                      }`}
                      onClick={() => setActivePack(p.id)}
                    >
                      {p.name}
                    </button>
                  ))}
                  <label className="text-xs text-accent-muted cursor-pointer block">
                    Import UI pack (.json)
                    <input
                      type="file"
                      accept="application/json,.json"
                      className="hidden"
                      onChange={async (e) => {
                        const f = e.target.files?.[0];
                        if (!f) return;
                        try {
                          const pack = JSON.parse(await f.text());
                          if (!pack.id || !pack.tokens) throw new Error("Invalid pack");
                          importPack(pack);
                          setActivePack(pack.id);
                        } catch (err) {
                          alert(String(err));
                        }
                      }}
                    />
                  </label>
                  <button
                    type="button"
                    className="text-xs text-slate-400"
                    onClick={() => {
                      const pack = exportActive();
                      if (!pack) return;
                      const blob = new Blob([JSON.stringify(pack, null, 2)], {
                        type: "application/json",
                      });
                      const a = document.createElement("a");
                      a.href = URL.createObjectURL(blob);
                      a.download = `${pack.name || "hearth-ui"}.json`;
                      a.click();
                    }}
                  >
                    Export current UI pack
                  </button>
                </div>
              </>
            )}

            {tab === "style" && (
              <>
                <p className="text-xs text-slate-500">
                  Model used for this chat only (overrides character/app default).
                </p>
                <select
                  className="w-full bg-surface-950 border border-slate-700 rounded-lg px-2 py-1.5 text-sm"
                  value={conversation.model_name || ""}
                  disabled={busy}
                  onChange={(e) => setModel(e.target.value)}
                >
                  <option value="">App / character default</option>
                  {models.map((m) => (
                    <option key={m} value={m}>
                      {m}
                    </option>
                  ))}
                </select>
              </>
            )}

            
            {tab === "intensity" && (
              <>
                <p className="text-xs text-slate-500">
                  How charged emotions should feel (0 = calm, 100 = peak drama).
                </p>
                <input
                  type="range"
                  min={0}
                  max={100}
                  defaultValue={Math.round(((conversation as any).emotion_intensity ?? 0.5) * 100)}
                  className="w-full accent-[var(--accent)]"
                  onMouseUp={async (e) => {
                    const v = parseInt((e.target as HTMLInputElement).value, 10) / 100;
                    await api.post(`/advanced/conversations/${conversation.id}/intensity`, {
                      value: v,
                    });
                    onConversationUpdate({
                      ...conversation,
                      emotion_intensity: v,
                    } as any);
                  }}
                />
                <p className="text-xs text-slate-400">
                  Or use /intensity 0-100 in chat.
                </p>
              </>
            )}

            {tab === "branches" && (
              <>
                <p className="text-xs text-slate-500">
                  Named timelines. /branch name creates one. Active branch is tracked on the chat.
                </p>
                
                <BranchPanel conversationId={conversation.id} />

              </>
            )}

            {tab === "persona" && (
              <>
                <p className="text-xs text-slate-500">
                  Switch who you are mid-chat. The character will react to the new persona.
                </p>
                {personas.map((p) => (
                  <button
                    key={p.id}
                    type="button"
                    disabled={busy}
                    onClick={() => switchPersona(p.id)}
                    className={`w-full text-left px-2 py-1.5 rounded-lg text-sm ${
                      conversation.persona_id === p.id
                        ? "bg-accent/20 text-accent-muted"
                        : "hover:bg-surface-800"
                    }`}
                  >
                    {p.profile_name}{" "}
                    <span className="text-slate-500">({p.chat_name})</span>
                  </button>
                ))}
              </>
            )}
          </div>
        </div>
      )}
    </div>
  );
}


function BranchPanel({ conversationId }: { conversationId: string }) {
  const [items, setItems] = useState<{ id: string; name: string; icon: string }[]>([]);
  const [name, setName] = useState("");
  useEffect(() => {
    api
      .get<{ id: string; name: string; icon: string }[]>(
        `/advanced/conversations/${conversationId}/branches`
      )
      .then(setItems)
      .catch(() => {});
  }, [conversationId]);
  return (
    <div className="space-y-2">
      {items.map((b) => (
        <button
          key={b.id}
          type="button"
          className="w-full text-left text-sm px-2 py-1 rounded hover:bg-surface-800"
          onClick={async () => {
            await api.post(
              `/advanced/conversations/${conversationId}/branches/${b.id}/activate`,
              {}
            );
          }}
        >
          {b.icon} {b.name}
        </button>
      ))}
      <div className="flex gap-1">
        <input
          className="flex-1 bg-surface-950 border border-slate-700 rounded px-2 py-1 text-xs"
          placeholder="New branch name"
          value={name}
          onChange={(e) => setName(e.target.value)}
        />
        <button
          type="button"
          className="text-xs text-accent-muted"
          onClick={async () => {
            if (!name.trim()) return;
            await api.post(`/advanced/conversations/${conversationId}/branches`, {
              name: name.trim(),
              icon: "🌿",
            });
            setName("");
            const list = await api.get<any[]>(
              `/advanced/conversations/${conversationId}/branches`
            );
            setItems(list);
          }}
        >
          Add
        </button>
      </div>
    </div>
  );
}
