/**
 * Chat markup parser.
 * Raw text → typed nodes. Never store rendered HTML as canonical content.
 */

export type NodeType =
  | "dialogue"
  | "action"
  | "important-action"
  | "emphasis"
  | "bullet"
  | "heading"
  | "text"
  | "break";

export interface MarkupNode {
  type: NodeType;
  text: string;
  /** For dialogue: speaker label if present before the em-dash line */
  speaker?: string;
}

/**
 * Parse roleplay markup into an ordered list of nodes.
 *
 * Dialogue:  — "Hello."
 * Action:    *walks to the door.*
 * Important: ***The room goes silent.***
 * Emphasis inside dialogue: **word**
 * Bullet:    * item  (star + space at line start)
 * Heading:   # Title
 */
export function parseMarkup(raw: string): MarkupNode[] {
  if (!raw) return [];
  const lines = raw.replace(/\r\n/g, "\n").split("\n");
  const nodes: MarkupNode[] = [];

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i];
    const trimmed = line.trim();

    if (!trimmed) {
      nodes.push({ type: "break", text: "" });
      continue;
    }

    // Heading: # Title
    if (/^#\s+/.test(trimmed)) {
      nodes.push({ type: "heading", text: trimmed.replace(/^#\s+/, "") });
      continue;
    }

    // Important action: ***...***
    const important = trimmed.match(/^\*{3}(.+?)\*{3}$/);
    if (important) {
      nodes.push({ type: "important-action", text: important[1].trim() });
      continue;
    }

    // Action: *...*  (no space after opening star, closing star at end)
    // Distinguish from bullet: bullet is "* " at start
    if (/^\*[^*+\s]/.test(trimmed) && trimmed.endsWith("*") && !trimmed.startsWith("* ")) {
      const inner = trimmed.slice(1, -1).trim();
      if (inner && !inner.includes("***")) {
        nodes.push({ type: "action", text: inner });
        continue;
      }
    }

    // Bullet: * item
    if (/^\*\s+/.test(trimmed)) {
      nodes.push({ type: "bullet", text: trimmed.replace(/^\*\s+/, "") });
      continue;
    }

    // Dialogue: — "..."  or — "..." with optional trailing text
    // Accept em-dash (—), en-dash (–), or double hyphen (--)
    const dialogueMatch = trimmed.match(
      /^(?:—|–|--)\s*[""](.+?)[""]\s*$/
    );
    if (dialogueMatch) {
      nodes.push({ type: "dialogue", text: dialogueMatch[1] });
      continue;
    }

    // Soft dialogue: line starts with em-dash and quote somewhere
    const softDialogue = trimmed.match(/^(?:—|–|--)\s*[""](.+)[""]/);
    if (softDialogue) {
      nodes.push({ type: "dialogue", text: softDialogue[1] });
      // leftover after closing quote
      const rest = trimmed.slice(trimmed.lastIndexOf(softDialogue[1]) + softDialogue[1].length + 1).replace(/^[""]\s*/, "").trim();
      if (rest) nodes.push({ type: "text", text: rest });
      continue;
    }

    // Plain text (may contain **emphasis** spans — split later at render/playback)
    nodes.push({ type: "text", text: trimmed });
  }

  return nodes;
}

/**
 * Split a string into plain / italic (*word*) / bold (**word**) segments.
 * ** is bold; single * is italic. Process bold first so it is not eaten as italic.
 */
export function splitEmphasis(
  text: string
): { emphasis: boolean; italic?: boolean; text: string }[] {
  const parts: { emphasis: boolean; italic?: boolean; text: string }[] = [];
  // Match **bold** or *italic* (non-greedy, no nested)
  const re = /\*\*(.+?)\*\*|\*([^*]+?)\*/g;
  let last = 0;
  let m: RegExpExecArray | null;
  while ((m = re.exec(text)) !== null) {
    if (m.index > last) {
      parts.push({ emphasis: false, text: text.slice(last, m.index) });
    }
    if (m[1] !== undefined) {
      parts.push({ emphasis: true, text: m[1] }); // bold
    } else if (m[2] !== undefined) {
      parts.push({ emphasis: false, italic: true, text: m[2] });
    }
    last = m.index + m[0].length;
  }
  if (last < text.length) {
    parts.push({ emphasis: false, text: text.slice(last) });
  }
  if (parts.length === 0) parts.push({ emphasis: false, text });
  return parts;
}

export interface PlaybackSettings {
  enabled: boolean;
  charsPerSecond: number;
  initialDelayMs: number;
  dialoguePauseMs: number;
  actionPauseMs: number;
  speakerPauseMs: number;
  headingPauseMs: number;
}

export const PLAYBACK_PRESETS: Record<string, Partial<PlaybackSettings>> = {
  Instant: { enabled: false },
  "Very Fast": { enabled: true, charsPerSecond: 90, dialoguePauseMs: 80, actionPauseMs: 120 },
  Fast: { enabled: true, charsPerSecond: 60, dialoguePauseMs: 120, actionPauseMs: 200 },
  Normal: { enabled: true, charsPerSecond: 40, dialoguePauseMs: 200, actionPauseMs: 400 },
  Slow: { enabled: true, charsPerSecond: 25, dialoguePauseMs: 350, actionPauseMs: 600 },
  "Very Slow": { enabled: true, charsPerSecond: 15, dialoguePauseMs: 500, actionPauseMs: 900 },
};

export const DEFAULT_PLAYBACK: PlaybackSettings = {
  enabled: true,
  charsPerSecond: 40,
  initialDelayMs: 300,
  dialoguePauseMs: 200,
  actionPauseMs: 400,
  speakerPauseMs: 500,
  headingPauseMs: 600,
};
