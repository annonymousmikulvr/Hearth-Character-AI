/**
 * Dev-mode slash commands for a single chat.
 * Only active when Settings → Dev mode is on.
 */

import { conversationsApi } from "../../api/conversations";
import { api } from "../../api/client";
import type { Conversation, Message } from "../../types";

export interface CommandContext {
  conversationId: string;
  conv: Conversation;
  messages: Message[];
  setMessages: (updater: (prev: Message[]) => Message[]) => void;
  reloadMessages: () => Promise<void>;
  regenerate: (messageId: string) => Promise<void>;
}

export interface CommandResult {
  ok: boolean;
  lines: string[];
}

type Handler = (
  args: string,
  ctx: CommandContext
) => Promise<CommandResult>;

const HELP: { cmd: string; desc: string }[] = [
  { cmd: "/help", desc: "List all dev commands" },
  { cmd: "/side [name]", desc: "Inject a test side-character bubble (default: Waiter)" },
  { cmd: "/side_gen [hint]", desc: "Ask the model to reply WITH a side character (JSON)" },
  { cmd: "/backstory", desc: "Force the AI to summarize persona + character + world facts" },
  { cmd: "/memory add <text>", desc: "Force-add a conversation memory for testing" },
  { cmd: "/memory list", desc: "List memories for this chat / persona / character" },
  { cmd: "/memory clear", desc: "Archive conversation-scoped memories" },
  { cmd: "/state", desc: "Show living character state (mood, relationship, notes)" },
  { cmd: "/vars", desc: "Show {{user}} / {{char}} resolved values" },
  { cmd: "/world", desc: "Show attached world summary" },
  { cmd: "/system <text>", desc: "Post a system note into the chat (not spoken as character)" },
  { cmd: "/as <name> <text>", desc: "Inject an assistant line as a named speaker" },
  { cmd: "/regen", desc: "Regenerate the last assistant (primary) message" },
  { cmd: "/ping", desc: "Test Ollama connection and default model" },
  { cmd: "/stats", desc: "Message counts and conversation ids" },
  { cmd: "/echo <text>", desc: "Echo text back as a local system note (no model)" },
];

async function localNote(
  ctx: CommandContext,
  text: string,
  role: "system" | "assistant" = "system",
  speaker = "Dev"
): Promise<void> {
  // Persist via user-facing APIs where possible
  if (role === "system") {
    const msg = await conversationsApi.postMessage(ctx.conversationId, {
      role: "system",
      raw_content: text,
      content_format: "plain",
    });
    ctx.setMessages((m) => [...m, msg]);
    return;
  }
  // For side/assistant test bubbles we POST system then show client-side only if needed —
  // Prefer server: store as assistant via a tiny backend path; fallback system-tagged.
  const msg = await conversationsApi.postMessage(ctx.conversationId, {
    role: "system",
    raw_content: `[${speaker}] ${text}`,
    content_format: "markup",
  });
  ctx.setMessages((m) => [...m, msg]);
}

const handlers: Record<string, Handler> = {
  help: async () => ({
    ok: true,
    lines: [
      "Hearth dev commands (this chat only):",
      ...HELP.map((h) => `  ${h.cmd.padEnd(28)} ${h.desc}`),
    ],
  }),

  side: async (args, ctx) => {
    const name = args.trim() || "Waiter";
    const text = `— "Excuse me — can I get you anything?"\n*${name} waits with a polite smile.*`;
    const msg = await api.post<Message>(`/conversations/${ctx.conversationId}/inject`, {
      speaker_type: "side",
      speaker_name: name,
      raw_content: text,
      role: "assistant",
    });
    ctx.setMessages((m) => [...m, msg]);
    return {
      ok: true,
      lines: [`Injected side character bubble: ${name}`],
    };
  },

  side_gen: async (args, ctx) => {
    const hint =
      args.trim() ||
      "Include at least one side character speaking in the scene (shopkeeper, passer-by, etc.).";
    await conversationsApi.postMessage(ctx.conversationId, {
      raw_content: `[DEV] ${hint}`,
    });
    const { messages } = await conversationsApi.generate(ctx.conversationId);
    ctx.setMessages((prev) => [...prev, ...messages]);
    await ctx.reloadMessages();
    return {
      ok: true,
      lines: [
        `Triggered generation with side-character hint.`,
        `Returned ${messages.length} message bubble(s).`,
      ],
    };
  },

  backstory: async (_args, ctx) => {
    const prompt =
      "[DEV BACKSTORY CHECK] In 5–8 short bullet points, list what you know about: " +
      "(1) the user's persona facts including family/relationships, " +
      "(2) your own character identity, " +
      "(3) the world if any. " +
      "Only use information from your system context — do not invent. " +
      "If a fact is missing, say so.";
    await conversationsApi.postMessage(ctx.conversationId, { raw_content: prompt });
    const { messages } = await conversationsApi.generate(ctx.conversationId);
    ctx.setMessages((prev) => {
      // reload will refresh; still append for responsiveness
      return prev;
    });
    await ctx.reloadMessages();
    return {
      ok: true,
      lines: [
        "Asked the model to summarize persona / character / world from context.",
        `Got ${messages.length} reply bubble(s). Check the chat.`,
      ],
    };
  },

  memory: async (args, ctx) => {
    const parts = args.trim().split(/\s+/);
    const sub = (parts[0] || "list").toLowerCase();
    if (sub === "add") {
      const text = parts.slice(1).join(" ").trim();
      if (!text) {
        return { ok: false, lines: ["Usage: /memory add <text>"] };
      }
      await api.post("/memories", {
        owner_type: "conversation",
        owner_id: ctx.conversationId,
        content: text,
        category: "fact",
        confidence: 1,
        importance: 0.9,
        tags: ["dev"],
      });
      // also character-scoped for stronger retrieval
      if (ctx.conv.character_id) {
        await api.post("/memories", {
          owner_type: "character",
          owner_id: ctx.conv.character_id,
          content: text,
          category: "fact",
          confidence: 1,
          importance: 0.85,
          tags: ["dev"],
        });
      }
      return { ok: true, lines: [`Memory added: ${text}`] };
    }
    if (sub === "list") {
      const all = await api.get<
        { id: string; content: string; owner_type: string; owner_id: string; importance: number }[]
      >("/memories?limit=200");
      const related = all.filter(
        (m) =>
          (m.owner_type === "conversation" && m.owner_id === ctx.conversationId) ||
          (m.owner_type === "character" && m.owner_id === ctx.conv.character_id) ||
          (m.owner_type === "persona" && m.owner_id === ctx.conv.persona_id) ||
          m.owner_type === "global"
      );
      // Filter tighter client-side using conversation id when present
      const lines = related.slice(0, 30).map(
        (m) => `• [${m.owner_type}] ${m.content} (imp ${m.importance})`
      );
      return {
        ok: true,
        lines: lines.length ? ["Memories:", ...lines] : ["No memories found."],
      };
    }
    if (sub === "clear") {
      const all = await api.get<{ id: string; owner_type: string; owner_id?: string }[]>(
        `/memories?owner_type=conversation&owner_id=${ctx.conversationId}&limit=200`
      );
      let n = 0;
      for (const m of all) {
        await api.delete(`/memories/${m.id}`);
        n++;
      }
      return { ok: true, lines: [`Archived ${n} conversation memories.`] };
    }
    return { ok: false, lines: ["Usage: /memory add|list|clear"] };
  },

  state: async (_args, ctx) => {
    // No dedicated GET yet — infer from settings endpoint or note
    return {
      ok: true,
      lines: [
        "Living character state is updated server-side after each exchange.",
        `Character: ${ctx.conv.character_name || ctx.conv.character_id}`,
        `Persona display: ${ctx.conv.persona_display_name}`,
        "Use /backstory to verify the model sees mood/relationship via prompt.",
      ],
    };
  },

  vars: async (_args, ctx) => ({
    ok: true,
    lines: [
      `{{user}} / {user} → ${ctx.conv.persona_display_name}`,
      `{{char}} / {char} → ${ctx.conv.character_name || ctx.conv.character_id}`,
      `persona_id → ${ctx.conv.persona_id}`,
      `character_id → ${ctx.conv.character_id}`,
      `world_id → ${ctx.conv.world_id || "(none)"}`,
    ],
  }),

  world: async (_args, ctx) => {
    if (!ctx.conv.world_id) {
      return { ok: true, lines: ["No world attached to this chat."] };
    }
    try {
      const w = await api.get<{
        name: string;
        description?: string;
        rules?: string;
      }>(`/worlds/${ctx.conv.world_id}`);
      return {
        ok: true,
        lines: [
          `World: ${w.name}`,
          w.description || "(no description)",
          w.rules ? `Rules: ${w.rules}` : "",
        ].filter(Boolean),
      };
    } catch (e) {
      return { ok: false, lines: [String(e)] };
    }
  },

  system: async (args, ctx) => {
    if (!args.trim()) return { ok: false, lines: ["Usage: /system <text>"] };
    await localNote(ctx, args.trim(), "system");
    return { ok: true, lines: ["System note posted."] };
  },

  as: async (args, ctx) => {
    const m = args.match(/^(\S+)\s+([\s\S]+)$/);
    if (!m) return { ok: false, lines: ["Usage: /as <name> <text>"] };
    const [, name, text] = m;
    const msg = await api.post<Message>(`/conversations/${ctx.conversationId}/inject`, {
      speaker_type: "side",
      speaker_name: name,
      raw_content: text,
      role: "assistant",
    });
    ctx.setMessages((prev) => [...prev, msg]);
    return { ok: true, lines: [`Injected as ${name}.`] };
  },

  regen: async (_args, ctx) => {
    const last = [...ctx.messages]
      .reverse()
      .find((m) => m.role === "assistant" && m.speaker_type !== "side");
    if (!last) return { ok: false, lines: ["No assistant message to regenerate."] };
    await ctx.regenerate(last.id);
    return { ok: true, lines: ["Regeneration requested."] };
  },

  ping: async () => {
    try {
      const c = await api.get<{
        available: boolean;
        models: string[];
        default_model: string;
        base_url: string;
      }>("/ai/connection");
      return {
        ok: c.available,
        lines: [
          `Ollama: ${c.available ? "connected" : "offline"}`,
          `URL: ${c.base_url}`,
          `Default model: ${c.default_model || "(none)"}`,
          `Models: ${(c.models || []).join(", ") || "(none)"}`,
        ],
      };
    } catch (e) {
      return { ok: false, lines: [String(e)] };
    }
  },

  stats: async (_args, ctx) => ({
    ok: true,
    lines: [
      `conversation_id: ${ctx.conversationId}`,
      `messages loaded: ${ctx.messages.length}`,
      `title: ${ctx.conv.title || "(untitled)"}`,
      `model override: ${ctx.conv.model_name || "(app default)"}`,
    ],
  }),

  echo: async (args) => ({
    ok: true,
    lines: [args || "(empty)"],
  }),
};

export async function runDevCommand(
  raw: string,
  ctx: CommandContext
): Promise<CommandResult> {
  const line = raw.trim();
  if (!line.startsWith("/")) {
    return { ok: false, lines: ["Not a command"] };
  }
  const without = line.slice(1);
  const space = without.indexOf(" ");
  const cmd = (space === -1 ? without : without.slice(0, space)).toLowerCase();
  const args = space === -1 ? "" : without.slice(space + 1);
  const handler = handlers[cmd];
  if (!handler) {
    return {
      ok: false,
      lines: [`Unknown command /${cmd}. Type /help for the list.`],
    };
  }
  return handler(args, ctx);
}

export function isDevCommand(text: string): boolean {
  return text.trim().startsWith("/");
}
