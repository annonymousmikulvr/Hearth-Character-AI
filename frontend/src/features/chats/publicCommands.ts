/**
 * Slash commands available to all users (no dev mode required).
 */

import { api } from "../../api/client";
import { conversationsApi } from "../../api/conversations";
import type { Conversation, Message } from "../../types";

export interface PubContext {
  conversationId: string;
  conv: Conversation;
  messages: Message[];
  setMessages: (u: (prev: Message[]) => Message[]) => void;
  reloadMessages: () => Promise<void>;
  regenerate: (messageId: string) => Promise<void>;
  onConversationUpdate?: (c: Conversation) => void;
}

export interface CmdResult {
  ok: boolean;
  lines: string[];
}

const HELP = [
  "/help — list commands",
  "/timeskip [description] — scene header time jump (separate from character speech)",
  "/scene <text> — insert a scene / world header message",
  "/pin <text> — pin a beat the model must respect",
  "/pins — list pinned beats",
  "/mute <topic> — never dwell on this topic",
  "/unmute <topic> — remove a mute",
  "/mutes — list muted topics",
  "/branch <name> — create & switch to a named branch",
  "/branches — list branches",
  "/intensity <0-100> — emotion intensity for this chat",
  "/filter <strict|moderate|mature|unfiltered> — content filter",
  "/as <Name> <line> — inject a side-character line",
  "/roster — list character side NPCs (if defined)",
  "/continue — bot keeps going without a new user line",
  "/side-test <Name> — fluency test: inject NPC then prompt model awareness",
  "/world-test — ask the model to speak a world-rule check line",
  "/age <n|+n> — temporary age for main character this chat",
  "/age-side <Name> <n|+n> — temporary age for a side character this chat",
  "/clothes <text> — temporary outfit for main character this chat",
  "/clothes-side <Name> <text> — temporary outfit for a side character",
  "/hint — suggest user replies (same as Hint button)",
  "/world <text> — insert a World lore/rule beat (distinct from Scene)",
];

export function isPublicCommand(text: string): boolean {
  const cmd = text.trim().slice(1).split(/\s+/)[0]?.toLowerCase();
  if (!text.trim().startsWith("/")) return false;
  const publicCmds = new Set([
    "help",
    "timeskip",
    "scene",
    "pin",
    "pins",
    "mute",
    "unmute",
    "mutes",
    "branch",
    "branches",
    "intensity",
    "filter",
    "as",
    "roster",
    "continue",
    "side-test",
    "world-test",
    "age",
    "age-side",
    "clothes",
    "clothes-side",
    "hint",
    "world",
  ]);
  return publicCmds.has(cmd || "");
}

export async function runPublicCommand(
  raw: string,
  ctx: PubContext
): Promise<CmdResult> {
  const line = raw.trim().slice(1);
  const space = line.indexOf(" ");
  const cmd = (space === -1 ? line : line.slice(0, space)).toLowerCase();
  const args = space === -1 ? "" : line.slice(space + 1).trim();
  const cid = ctx.conversationId;

  switch (cmd) {
    case "help":
      return { ok: true, lines: ["Commands:", ...HELP] };

    case "timeskip": {
      const text = args
        ? `— Time skip —\n${args}`
        : "— Time skip —\nLater…";
      const msg = await api.post<Message>(`/advanced/conversations/${cid}/scene`, {
        text,
      });
      ctx.setMessages((m) => [...m, msg as any]);
      await ctx.reloadMessages();
      return { ok: true, lines: ["Inserted time-skip scene header."] };
    }

    case "world": {
      if (!args) return { ok: false, lines: ["Usage: /world <lore or rule beat>"] };
      const msg = await api.post(`/conversations/${cid}/inject`, {
        speaker_type: "system",
        speaker_name: "World",
        raw_content: args,
        role: "system",
      });
      ctx.setMessages((m) => [...m, msg as any]);
      await ctx.reloadMessages();
      return { ok: true, lines: ["World beat inserted."] };
    }

    case "scene": {
      if (!args) return { ok: false, lines: ["Usage: /scene <text>"] };
      const msg = await api.post<Message>(`/advanced/conversations/${cid}/scene`, {
        text: args,
      });
      ctx.setMessages((m) => [...m, msg as any]);
      await ctx.reloadMessages();
      return { ok: true, lines: ["Scene header added."] };
    }

    case "pin": {
      if (!args) return { ok: false, lines: ["Usage: /pin <text>"] };
      const r = await api.post<{ pins: string[] }>(
        `/advanced/conversations/${cid}/pins`,
        { text: args }
      );
      return { ok: true, lines: [`Pinned. Total: ${r.pins.length}`, ...r.pins.slice(-5).map((p) => `• ${p}`)] };
    }

    case "pins": {
      const r = await api.get<{ pins: string[] }>(
        `/advanced/conversations/${cid}/pins`
      );
      return {
        ok: true,
        lines: r.pins.length ? ["Pins:", ...r.pins.map((p) => `• ${p}`)] : ["No pins."],
      };
    }

    case "mute": {
      if (!args) return { ok: false, lines: ["Usage: /mute <topic>"] };
      const r = await api.post<{ mutes: string[] }>(
        `/advanced/conversations/${cid}/mutes`,
        { topic: args }
      );
      return { ok: true, lines: [`Muted. List: ${r.mutes.join(", ") || "(empty)"}`] };
    }

    case "unmute": {
      if (!args) return { ok: false, lines: ["Usage: /unmute <topic>"] };
      const r = await api.delete<{ mutes: string[] }>(
        `/advanced/conversations/${cid}/mutes/${encodeURIComponent(args)}`
      );
      return { ok: true, lines: [`Updated mutes: ${r.mutes.join(", ") || "(none)"}`] };
    }

    case "mutes": {
      const r = await api.get<{ mutes: string[] }>(
        `/advanced/conversations/${cid}/mutes`
      );
      return {
        ok: true,
        lines: r.mutes.length
          ? ["Muted topics:", ...r.mutes.map((m) => `• ${m}`)]
          : ["No mutes."],
      };
    }

    case "branch": {
      if (!args) return { ok: false, lines: ["Usage: /branch <name>"] };
      const last = [...ctx.messages].reverse().find((m) => m.role === "assistant");
      const b = await api.post<{ id: string; name: string; icon: string }>(
        `/advanced/conversations/${cid}/branches`,
        { name: args, icon: "🌿", from_message_id: last?.id }
      );
      return { ok: true, lines: [`Branch “${b.name}” ${b.icon} created and activated.`] };
    }

    case "branches": {
      const list = await api.get<{ id: string; name: string; icon: string }[]>(
        `/advanced/conversations/${cid}/branches`
      );
      return {
        ok: true,
        lines: list.length
          ? ["Branches:", ...list.map((b) => `${b.icon} ${b.name}`)]
          : ["No named branches yet. Use /branch <name>."],
      };
    }

    case "intensity": {
      const n = parseInt(args, 10);
      if (Number.isNaN(n) || n < 0 || n > 100) {
        return { ok: false, lines: ["Usage: /intensity <0-100>"] };
      }
      const r = await api.post<{ emotion_intensity: number }>(
        `/advanced/conversations/${cid}/intensity`,
        { value: n / 100 }
      );
      if (ctx.onConversationUpdate) {
        ctx.onConversationUpdate({
          ...ctx.conv,
          emotion_intensity: r.emotion_intensity,
        } as any);
      }
      return { ok: true, lines: [`Intensity set to ${n}%.`] };
    }

    case "filter": {
      const lvl = args.toLowerCase();
      if (!["strict", "moderate", "mature", "unfiltered"].includes(lvl)) {
        return {
          ok: false,
          lines: ["Usage: /filter strict|moderate|mature|unfiltered"],
        };
      }
      const updated = await conversationsApi.update(cid, {
        filter_level: lvl,
      } as any);
      ctx.onConversationUpdate?.({ ...ctx.conv, ...updated, filter_level: lvl });
      return { ok: true, lines: [`Filter set to ${lvl}.`] };
    }

    case "as": {
      const m = args.match(/^(\S+)\s+([\s\S]+)$/);
      if (!m) return { ok: false, lines: ["Usage: /as <Name> <line>"] };
      const msg = await api.post(`/conversations/${cid}/inject`, {
        speaker_type: "side",
        speaker_name: m[1],
        raw_content: m[2],
        role: "assistant",
      });
      ctx.setMessages((prev) => [...prev, msg as any]);
      return { ok: true, lines: [`Injected as ${m[1]}.`] };
    }

    case "roster": {
      try {
        const ch = await api.get<{ side_roster?: { name: string; notes?: string }[] }>(
          `/characters/${ctx.conv.character_id}`
        );
        const roster = ch.side_roster || [];
        if (!roster.length) {
          return {
            ok: true,
            lines: [
              "No side roster on this character. Add NPCs in the character editor (Side roster).",
            ],
          };
        }
        return {
          ok: true,
          lines: [
            "Side roster:",
            ...roster.map(
              (n) => `• ${n.name}${n.notes ? ` — ${n.notes}` : ""}`
            ),
          ],
        };
      } catch (e) {
        return { ok: false, lines: [String(e)] };
      }
    }


    case "hint": {
      const res = await api.post<{ hints: string[] }>(
        `/conversations/${cid}/hint?count=3`,
        {}
      );
      return {
        ok: true,
        lines: [
          "Suggested replies (copy into the box, or use the Hint button next time):",
          ...(res.hints || []).map((h, i) => `${i + 1}. ${h}`),
        ],
      };
    }

    case "continue": {
      await api.post(`/conversations/${cid}/continue`, {});
      await ctx.reloadMessages();
      return { ok: true, lines: ["Continued from last beat."] };
    }

    case "side-test": {
      const name = args.trim() || "Chika";
      await api.post(`/conversations/${cid}/inject`, {
        speaker_type: "side",
        speaker_name: name,
        raw_content: `*${name} watches quietly, then clears their throat.* — "I'm here. Don't pretend you don't see me."`,
        role: "assistant",
      });
      // cue model on next reply via pin
      await api.post(`/advanced/conversations/${cid}/pins`, {
        text: `Side character ${name} is present in the scene and can speak/react naturally.`,
      });
      await ctx.reloadMessages();
      return {
        ok: true,
        lines: [
          `Injected side character "${name}".`,
          "Pinned presence note. Send a message or /continue — the main character should acknowledge them.",
        ],
      };
    }

    case "world-test": {
      await api.post(`/conversations/${cid}/inject`, {
        speaker_type: "system",
        speaker_name: "World",
        raw_content:
          "[World check] Briefly prove you know the active world rules (one short action + one short line). If no world is attached, state that no world is bound to this chat.",
        role: "system",
      });
      await ctx.reloadMessages();
      return {
        ok: true,
        lines: [
          "World-test cue inserted. Press Continue or send a message to see if the bot reflects world rules.",
        ],
      };
    }

    case "age": {
      if (!args) return { ok: false, lines: ["Usage: /age 19   or   /age +1"] };
      const body: any = {};
      if (args.startsWith("+") || args.startsWith("-")) {
        body.age_delta = parseInt(args, 10);
      } else {
        body.age = args;
      }
      const r = await api.post(`/advanced/conversations/${cid}/live-overrides`, body);
      return { ok: true, lines: [`Chat-only age state: ${JSON.stringify(r)}`] };
    }

    case "age-side": {
      const m = args.match(/^(\S+)\s+(.+)$/);
      if (!m) return { ok: false, lines: ["Usage: /age-side Name 17   or   /age-side Name +1"] };
      const body: any = { side_name: m[1] };
      const rest = m[2].trim();
      if (rest.startsWith("+") || rest.startsWith("-")) body.age_delta = parseInt(rest, 10);
      else body.side_age = rest;
      const r = await api.post(`/advanced/conversations/${cid}/live-overrides`, body);
      return { ok: true, lines: [`Side age updated: ${JSON.stringify(r)}`] };
    }

    case "clothes": {
      if (!args) return { ok: false, lines: ["Usage: /clothes black coat over school uniform"] };
      const r = await api.post(`/advanced/conversations/${cid}/live-overrides`, {
        clothes: args,
      });
      return { ok: true, lines: [`Chat-only clothes: ${r.clothes || args}`] };
    }

    case "clothes-side": {
      const m = args.match(/^(\S+)\s+(.+)$/);
      if (!m) return { ok: false, lines: ["Usage: /clothes-side Name red hoodie"] };
      const r = await api.post(`/advanced/conversations/${cid}/live-overrides`, {
        side_name: m[1],
        side_clothes: m[2],
      });
      return { ok: true, lines: [`Side clothes updated for ${m[1]}`] };
    }

    default:
      return { ok: false, lines: [`Unknown command /${cmd}. Try /help.`] };
  }
}
