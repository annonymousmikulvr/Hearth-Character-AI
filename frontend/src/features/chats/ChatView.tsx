import { useEffect, useRef, useState, useCallback } from "react";
import { Link, useParams } from "react-router-dom";
import { conversationsApi } from "../../api/conversations";
import type { Conversation, Message } from "../../types";
import { inputClass } from "../../components/FormField";
import {
  MessagePlayback,
  MessageStatic,
} from "../../components/MessagePlayback";
import { DEFAULT_PLAYBACK } from "../../parser/markup";
import { useDevStore } from "../../stores/devStore";
import { isDevCommand, runDevCommand } from "./devCommands";
import { isPublicCommand, runPublicCommand } from "./publicCommands";
import { api } from "../../api/client";
import ChatOptionsPanel from "./ChatOptionsPanel";
import { useUiPackStore } from "../../stores/uiPackStore";

type ResponseState = "idle" | "generating" | "processing" | "error";

export default function ChatView() {
  const { id } = useParams<{ id: string }>();
  const [conv, setConv] = useState<Conversation | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [draft, setDraft] = useState("");
  const [state, setState] = useState<ResponseState>("idle");
  const [error, setError] = useState<string | null>(null);
  const [playIds, setPlayIds] = useState<Set<string>>(new Set());
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editText, setEditText] = useState("");
  const [variantInfo, setVariantInfo] = useState<
    Record<string, { index: number; total: number; ids: string[] }>
  >({});
  const [devLog, setDevLog] = useState<string[] | null>(null);
  const [toneForId, setToneForId] = useState<string | null>(null);
  const [ratingFlash, setRatingFlash] = useState<Record<string, number>>({});
  const [hints, setHints] = useState<string[] | null>(null);
  const [hintBusy, setHintBusy] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);
  const busy = state === "generating" || state === "processing";
  const devMode = useDevStore((s) => s.devMode);
  const chatLayout = useUiPackStore((s) => s.chatLayout);
  const chatWallpaper = useUiPackStore((s) => s.chatWallpaper);

  const reloadMessages = useCallback(async () => {
    if (!id) return;
    const msgs = await conversationsApi.listMessages(id);
    setMessages(msgs);
    const info: Record<string, { index: number; total: number; ids: string[] }> =
      {};
    for (const m of msgs) {
      if (m.role !== "assistant" || m.speaker_type === "side") continue;
      try {
        const variants = await conversationsApi.listVariants(id, m.id);
        if (variants.length > 1) {
          const selectedIdx = variants.findIndex((v) => v.id === m.id);
          info[m.id] = {
            index: selectedIdx >= 0 ? selectedIdx : 0,
            total: variants.length,
            ids: variants.map((v) => v.id),
          };
        }
      } catch {
        /* ignore */
      }
    }
    setVariantInfo(info);
  }, [id]);

  useEffect(() => {
    if (!id) return;
    Promise.all([conversationsApi.get(id), conversationsApi.listMessages(id)])
      .then(([c, msgs]) => {
        setConv(c);
        setMessages(msgs);
      })
      .catch((e) => setError(String(e)));
  }, [id]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, state, devLog]);

  async function loadHints() {
    if (!id || hintBusy) return;
    setHintBusy(true);
    setError(null);
    try {
      const res = await api.post<{ hints: string[] }>(
        `/conversations/${id}/hint?count=3`,
        {}
      );
      setHints(res.hints || []);
    } catch (e) {
      setError(String(e));
    } finally {
      setHintBusy(false);
    }
  }

  async function continueChat() {
    if (!id || state === "processing") return;
    setState("processing");
    setError(null);
    try {
      const { messages: assistantMsgs } = await api.post<{ messages: Message[] }>(
        `/conversations/${id}/continue`,
        {}
      );
      setMessages((prev) => {
        const next = [...prev];
        for (const m of assistantMsgs) {
          if (!next.find((x) => x.id === m.id)) next.push(m);
        }
        return next;
      });
      setState("playback");
    } catch (e) {
      setError(String(e));
      setState("idle");
    }
  }

  async function regenerate(messageId: string) {
    if (!id || busy) return;
    setError(null);
    setState("processing");
    try {
      const { messages: newMsgs } = await conversationsApi.regenerate(
        id,
        messageId
      );
      setPlayIds(new Set(newMsgs.map((x) => x.id)));
      await reloadMessages();
      setState("idle");
    } catch (e) {
      setError(String(e));
      setState("error");
    }
  }

  async function swipeVariant(messageId: string, direction: -1 | 1) {
    if (!id) return;
    const info = variantInfo[messageId];
    if (!info) return;
    const next = info.index + direction;
    if (next < 0 || next >= info.total) return;
    const targetId = info.ids[next];
    try {
      await conversationsApi.selectVariant(id, targetId);
      await reloadMessages();
    } catch (e) {
      setError(String(e));
    }
  }

  async function saveEdit(messageId: string) {
    if (!id || !editText.trim()) return;
    try {
      await conversationsApi.editMessage(id, messageId, editText.trim());
      setEditingId(null);
      await reloadMessages();
    } catch (e) {
      setError(String(e));
    }
  }

  async function send() {
    if (!id || !draft.trim() || busy) return;
    const text = draft.trim();

    // Public slash commands (always)
    if (isPublicCommand(text)) {
      setDraft("");
      setDevLog(null);
      setError(null);
      try {
        const result = await runPublicCommand(text, {
          conversationId: id,
          conv: conv!,
          messages,
          setMessages,
          reloadMessages,
          regenerate,
          onConversationUpdate: setConv,
        });
        setDevLog(result.lines);
      } catch (e) {
        setError(String(e));
      }
      return;
    }
    if (devMode && isDevCommand(text)) {
      setDraft("");
      setDevLog(null);
      setError(null);
      try {
        const result = await runDevCommand(text, {
          conversationId: id,
          conv: conv!,
          messages,
          setMessages,
          reloadMessages,
          regenerate,
        });
        setDevLog(result.lines);
      } catch (e) {
        setError(String(e));
      }
      return;
    }

    setDraft("");
    setError(null);
    setDevLog(null);
    setState("generating");
    try {
      let expanded = text;
      if (conv) {
        const u = conv.persona_display_name || "User";
        const c = conv.character_name || "Character";
        expanded = expanded
          .replace(/\{\{\s*user\s*\}\}/gi, u)
          .replace(/\{\s*user\s*\}/gi, u)
          .replace(/\{\{\s*char(?:acter)?\s*\}\}/gi, c)
          .replace(/\{\s*char(?:acter)?\s*\}/gi, c);
      }
      const userMsg = await conversationsApi.postMessage(id, {
        raw_content: expanded,
      });
      setMessages((m) => [...m, userMsg]);
      setState("processing");
      const { messages: assistantMsgs } = await conversationsApi.generate(id);
      setPlayIds(new Set(assistantMsgs.map((x) => x.id)));
      setMessages((m) => [...m, ...assistantMsgs]);
      setState("idle");
      await reloadMessages();
    } catch (e) {
      setError(String(e));
      setState("error");
    }
  }

  if (error && !conv) {
    return (
      <div className="text-sm text-red-400">
        {error}{" "}
        <Link to="/chats" className="underline text-accent-muted">
          Back to chats
        </Link>
      </div>
    );
  }

  if (!conv) {
    return <p className="text-slate-400 text-sm">Loading chat…</p>;
  }

  const statusLabel =
    state === "generating"
      ? `${conv.character_name || "Character"} is typing…`
      : state === "processing"
        ? `${conv.character_name || "Character"} is preparing a response…`
        : null;

  return (
    <div className="flex flex-col h-[calc(100vh-5.5rem)] max-w-3xl mx-auto">
      <div className="flex items-center gap-3 pb-2 border-b border-slate-800 shrink-0">
        <Link to="/chats" className="text-slate-400 hover:text-white text-sm">
          ← Chats
        </Link>
        <div className="min-w-0 flex-1">
          <h1 className="font-semibold truncate">
            {conv.title || `Chat with ${conv.character_name}`}
          </h1>
          <p className="text-xs text-slate-400">
            {conv.character_name}
            {" · "}
            you as {conv.persona_display_name}
            {" · "}
            {conv.filter_level || "mature"}
            {devMode ? " · dev" : ""}
          </p>
        </div>
      </div>

      <div
        className={`flex-1 overflow-y-auto py-2 ${chatLayout === "compact" ? "space-y-1.5" : chatLayout === "theater" ? "space-y-4 max-w-2xl mx-auto w-full" : "space-y-2.5"}`}
        style={chatWallpaper ? { background: chatWallpaper, backgroundSize: "cover" } : undefined}
      >
        {messages.map((m) => {
          const isUser = m.speaker_type === "user" || m.role === "user";
          const isSide = m.speaker_type === "side";
          const isSystem = m.role === "system" || m.speaker_type === "system";
          const animate = playIds.has(m.id);
          const vInfo = variantInfo[m.id];

          return (
            <div
              key={m.id}
              className={`flex ${isUser ? "justify-end" : "justify-start"} group`}
            >
              <div
                className={`max-w-[85%] rounded-2xl px-4 py-2.5 text-sm leading-relaxed ${
                  isUser
                    ? "bg-accent/20 border border-accent/30 text-slate-100"
                    : isSystem
                      ? m.speaker_name === "Scene"
                        ? "w-full max-w-full bg-transparent border-0 text-center text-slate-400 text-xs italic tracking-wide py-1"
                        : m.speaker_name === "World"
                        ? "w-full max-w-full rounded-lg border border-emerald-900/50 bg-emerald-950/20 text-emerald-200/90 text-xs px-3 py-2"
                        : "bg-surface-800/50 border border-dashed border-slate-700 text-slate-400 text-xs font-mono"
                      : isSide
                        ? "bg-surface-800/80 border border-slate-700 text-slate-200"
                        : "bg-surface-900 border border-slate-800 text-slate-200"
                }`}
              >
                {!isUser && (
                  <div className="text-xs font-medium text-accent-muted mb-1">
                    {m.speaker_name}
                    {isSide && (
                      <span className="text-slate-500 font-normal"> · side</span>
                    )}
                    {isSystem && (
                      <span className="text-slate-500 font-normal"> · system</span>
                    )}
                  </div>
                )}

                {editingId === m.id ? (
                  <div className="space-y-2">
                    <textarea
                      className={`${inputClass} min-h-[80px]`}
                      value={editText}
                      onChange={(e) => setEditText(e.target.value)}
                    />
                    <div className="flex gap-2">
                      <button
                        type="button"
                        onClick={() => saveEdit(m.id)}
                        className="text-xs px-2 py-1 rounded bg-accent text-white"
                      >
                        Save
                      </button>
                      <button
                        type="button"
                        onClick={() => setEditingId(null)}
                        className="text-xs px-2 py-1 rounded text-slate-400"
                      >
                        Cancel
                      </button>
                    </div>
                  </div>
                ) : animate ? (
                  <MessagePlayback
                    rawContent={m.raw_content}
                    settings={DEFAULT_PLAYBACK}
                    onComplete={() =>
                      setPlayIds((prev) => {
                        const n = new Set(prev);
                        n.delete(m.id);
                        return n;
                      })
                    }
                  />
                ) : (
                  <MessageStatic rawContent={m.raw_content} />
                )}

                {!busy && editingId !== m.id && !isSystem && (
                  <div className="flex flex-wrap items-center gap-2 mt-2 opacity-0 group-hover:opacity-100 transition-opacity">
                    <button
                      type="button"
                      className="text-[11px] text-slate-500 hover:text-slate-300"
                      onClick={() => {
                        setEditingId(m.id);
                        setEditText(m.raw_content);
                      }}
                    >
                      Edit
                    </button>
                    {m.role === "assistant" && m.speaker_type !== "side" && (
                      <>
                        <button
                          type="button"
                          className="text-[11px] text-slate-500 hover:text-slate-300"
                          onClick={() => {
                            setToneForId(m.id);
                            regenerate(m.id);
                          }}
                        >
                          Regenerate
                        </button>
                        {toneForId === m.id &&
                          (["soft", "sharp", "playful"] as const).map((tone) => (
                            <button
                              key={tone}
                              type="button"
                              className="text-[11px] text-slate-500 hover:text-slate-300"
                              onClick={async () => {
                                if (!id) return;
                                setState("processing");
                                try {
                                  await api.post(
                                    `/advanced/conversations/${id}/messages/${m.id}/tone-regen`,
                                    { tone }
                                  );
                                  await reloadMessages();
                                } catch (e) {
                                  setError(String(e));
                                } finally {
                                  setState("idle");
                                }
                              }}
                            >
                              {tone}
                            </button>
                          ))}
                        <button
                          type="button"
                          className={`text-[11px] ${ratingFlash[m.id] === 1 ? "text-emerald-400" : "text-slate-500 hover:text-emerald-400"}`}
                          onClick={async () => {
                            if (!id) return;
                            try {
                              await api.post(
                                `/advanced/conversations/${id}/messages/${m.id}/rate`,
                                { rating: 1 }
                              );
                              setRatingFlash((f) => ({ ...f, [m.id]: 1 }));
                            } catch (e) {
                              setError(String(e));
                            }
                          }}
                        >
                          ▲
                        </button>
                        <button
                          type="button"
                          className={`text-[11px] ${ratingFlash[m.id] === -1 ? "text-red-400" : "text-slate-500 hover:text-red-400"}`}
                          onClick={async () => {
                            if (!id) return;
                            try {
                              await api.post(
                                `/advanced/conversations/${id}/messages/${m.id}/rate`,
                                { rating: -1 }
                              );
                              setRatingFlash((f) => ({ ...f, [m.id]: -1 }));
                            } catch (e) {
                              setError(String(e));
                            }
                          }}
                        >
                          ▼
                        </button>
                        <button
                          type="button"
                          className="text-[11px] text-slate-500 hover:text-amber-300"
                          onClick={async () => {
                            if (!id) return;
                            await api.post(`/advanced/conversations/${id}/pins`, {
                              text: m.raw_content.slice(0, 500),
                            });
                            setDevLog(["Pinned this message beat."]);
                          }}
                        >
                          Pin
                        </button>
                      </>
                    )}
                    <button
                      type="button"
                      className="text-[11px] text-slate-500 hover:text-red-400"
                      onClick={async () => {
                        if (!id || !confirm("Delete this message?")) return;
                        await conversationsApi.deleteMessage(id, m.id);
                        await reloadMessages();
                      }}
                    >
                      Delete
                    </button>
                    <button
                      type="button"
                      className="text-[11px] text-slate-500 hover:text-amber-400"
                      title="Remove all messages after this one"
                      onClick={async () => {
                        if (!id || !confirm("Jump back here? All later messages will be deleted.")) return;
                        await conversationsApi.rewind(id, m.id, true);
                        await reloadMessages();
                      }}
                    >
                      Jump here
                    </button>
                    <button
                      type="button"
                      className="text-[11px] text-slate-500 hover:text-amber-400"
                      title="Delete this message and everything after"
                      onClick={async () => {
                        if (!id || !confirm("Rewind before this message? It and all later messages will be deleted.")) return;
                        await conversationsApi.rewind(id, m.id, false);
                        await reloadMessages();
                      }}
                    >
                      Rewind before
                    </button>
                    {vInfo && (
                      <span className="text-[11px] text-slate-500 flex items-center gap-1">
                        <button
                          type="button"
                          disabled={vInfo.index <= 0}
                          onClick={() => swipeVariant(m.id, -1)}
                          className="hover:text-white disabled:opacity-30"
                        >
                          ←
                        </button>
                        {vInfo.index + 1} / {vInfo.total}
                        <button
                          type="button"
                          disabled={vInfo.index >= vInfo.total - 1}
                          onClick={() => swipeVariant(m.id, 1)}
                          className="hover:text-white disabled:opacity-30"
                        >
                          →
                        </button>
                      </span>
                    )}
                  </div>
                )}
              </div>
            </div>
          );
        })}

        {statusLabel && (
          <div className="flex justify-start">
            <div className="text-sm text-slate-400 italic px-2">{statusLabel}</div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      {devLog && (
        <div className="text-xs mb-2 rounded-md px-3 py-2 border border-slate-700 bg-surface-900 font-mono whitespace-pre-wrap text-slate-300">
          {devLog.join("\n")}
        </div>
      )}
      {devMode && (
        <div className="text-[10px] text-slate-500 mb-1">
          Dev mode · type /help for commands
        </div>
      )}
      {error && (
        <div className="text-xs text-red-400 mb-2 bg-red-950/30 border border-red-900/50 rounded-md px-3 py-2">
          {error}
        </div>
      )}

      {hints && hints.length > 0 && (
        <div className="shrink-0 mb-2 rounded-xl border border-slate-700 bg-surface-900 p-2 space-y-1.5">
          <div className="flex items-center justify-between px-1">
            <span className="text-[11px] text-slate-400">
              Suggested replies (tap to use — edit before sending)
            </span>
            <button
              type="button"
              className="text-[11px] text-slate-500 hover:text-slate-300"
              onClick={() => setHints(null)}
            >
              Close
            </button>
          </div>
          {hints.map((h, i) => (
            <button
              key={i}
              type="button"
              onClick={() => {
                setDraft(h);
                setHints(null);
              }}
              className="w-full text-left text-sm px-2.5 py-2 rounded-lg bg-surface-950 border border-slate-800 hover:border-accent/40 text-slate-200"
            >
              {h}
            </button>
          ))}
          <button
            type="button"
            className="text-[11px] text-accent-muted px-1"
            onClick={loadHints}
            disabled={hintBusy}
          >
            Refresh hints
          </button>
        </div>
      )}
      <div className="shrink-0 pt-3 border-t border-slate-800 flex gap-2 items-end">
        {conv && (
          <ChatOptionsPanel
            conversation={conv}
            onConversationUpdate={setConv}
          />
        )}
        <textarea
          className={`${inputClass} min-h-[44px] max-h-32 resize-y flex-1`}
          rows={1}
          placeholder={
            busy
              ? "Waiting for reply…"
              : "Message or /command… (/help)"
          }
          value={draft}
          disabled={busy}
          onChange={(e) => setDraft(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter" && !e.shiftKey) {
              e.preventDefault();
              send();
            }
          }}
        />
        <button
          type="button"
          disabled={busy || !draft.trim()}
          onClick={send}
          className="px-4 rounded-md bg-accent hover:bg-accent-hover text-sm font-medium disabled:opacity-40 self-end h-11"
        >
          {busy ? "…" : "Send"}
        </button>
      </div>
    </div>
  );
}
