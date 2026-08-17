import { create } from "zustand";

export interface UiPack {
  id: string;
  name: string;
  version: number;
  description?: string;
  tokens: {
    bg?: string;
    bgElevated?: string;
    border?: string;
    text?: string;
    textMuted?: string;
    accent?: string;
    accentHover?: string;
    userBubble?: string;
    radius?: string;
    font?: string;
    chatWallpaper?: string; // CSS background value or url()
    chatLayout?: "classic" | "compact" | "bubble" | "theater";
  };
}

interface UiPackState {
  packs: UiPack[];
  activePackId: string | null;
  chatLayout: "classic" | "compact" | "bubble" | "theater";
  chatWallpaper: string;
  setActivePack: (id: string | null) => void;
  setChatLayout: (l: UiPack["tokens"]["chatLayout"]) => void;
  setChatWallpaper: (w: string) => void;
  importPack: (pack: UiPack) => void;
  removePack: (id: string) => void;
  exportActive: () => UiPack | null;
}

function loadPacks(): UiPack[] {
  try {
    return JSON.parse(localStorage.getItem("hearth-ui-packs") || "[]");
  } catch {
    return [];
  }
}

function loadActive(): string | null {
  try {
    return localStorage.getItem("hearth-ui-active");
  } catch {
    return null;
  }
}

function applyPackTokens(pack: UiPack | null) {
  if (typeof document === "undefined") return;
  const root = document.documentElement;
  if (!pack) return;
  const t = pack.tokens;
  if (t.bg) root.style.setProperty("--bg", t.bg);
  if (t.bgElevated) root.style.setProperty("--bg-elevated", t.bgElevated);
  if (t.border) root.style.setProperty("--border", t.border);
  if (t.text) root.style.setProperty("--text", t.text);
  if (t.textMuted) root.style.setProperty("--text-muted", t.textMuted);
  if (t.accent) {
    root.style.setProperty("--accent", t.accent);
    root.style.setProperty("--accent-hover", t.accentHover || t.accent);
    root.style.setProperty("--accent-muted", t.accent);
  }
}

export const useUiPackStore = create<UiPackState>((set, get) => ({
  packs: loadPacks(),
  activePackId: loadActive(),
  chatLayout:
    (localStorage.getItem("hearth-chat-layout") as UiPackState["chatLayout"]) ||
    "classic",
  chatWallpaper: localStorage.getItem("hearth-chat-wallpaper") || "",
  setActivePack: (id) => {
    localStorage.setItem("hearth-ui-active", id || "");
    const pack = get().packs.find((p) => p.id === id) || null;
    applyPackTokens(pack);
    if (pack?.tokens.chatLayout) {
      localStorage.setItem("hearth-chat-layout", pack.tokens.chatLayout);
      set({ chatLayout: pack.tokens.chatLayout });
    }
    if (pack?.tokens.chatWallpaper) {
      localStorage.setItem("hearth-chat-wallpaper", pack.tokens.chatWallpaper);
      set({ chatWallpaper: pack.tokens.chatWallpaper });
    }
    set({ activePackId: id });
  },
  setChatLayout: (chatLayout) => {
    if (!chatLayout) return;
    localStorage.setItem("hearth-chat-layout", chatLayout);
    set({ chatLayout });
  },
  setChatWallpaper: (chatWallpaper) => {
    localStorage.setItem("hearth-chat-wallpaper", chatWallpaper);
    set({ chatWallpaper });
  },
  importPack: (pack) => {
    const packs = [...get().packs.filter((p) => p.id !== pack.id), pack];
    localStorage.setItem("hearth-ui-packs", JSON.stringify(packs));
    set({ packs });
  },
  removePack: (id) => {
    const packs = get().packs.filter((p) => p.id !== id);
    localStorage.setItem("hearth-ui-packs", JSON.stringify(packs));
    if (get().activePackId === id) {
      localStorage.removeItem("hearth-ui-active");
      set({ activePackId: null });
    }
    set({ packs });
  },
  exportActive: () => {
    const id = get().activePackId;
    if (!id) {
      return {
        id: "hearth-current",
        name: "Current Hearth UI",
        version: 1,
        tokens: {
          chatLayout: get().chatLayout,
          chatWallpaper: get().chatWallpaper,
        },
      };
    }
    return get().packs.find((p) => p.id === id) || null;
  },
}));

export function applyStoredUiPack() {
  const id = loadActive();
  if (!id) return;
  const packs = loadPacks();
  const pack = packs.find((p) => p.id === id);
  if (pack) applyPackTokens(pack);
}
