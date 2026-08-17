import { create } from "zustand";

export type ThemeId = "midnight" | "slate" | "ember" | "forest" | "ocean" | "light";

export interface ThemeDef {
  id: ThemeId;
  label: string;
  description: string;
}

export const THEMES: ThemeDef[] = [
  { id: "midnight", label: "Midnight", description: "Deep violet dark (default)" },
  { id: "slate", label: "Slate", description: "Cool neutral dark" },
  { id: "ember", label: "Ember", description: "Warm charcoal & amber" },
  { id: "forest", label: "Forest", description: "Deep green" },
  { id: "ocean", label: "Ocean", description: "Blue-teal dark" },
  { id: "light", label: "Light", description: "Clean light mode" },
];

function loadTheme(): ThemeId {
  try {
    const t = localStorage.getItem("lcai-theme") as ThemeId | null;
    if (t && THEMES.some((x) => x.id === t)) return t;
  } catch { /* ignore */ }
  return "midnight";
}

interface ThemeState {
  theme: ThemeId;
  setTheme: (t: ThemeId) => void;
}

export const useThemeStore = create<ThemeState>((set) => ({
  theme: loadTheme(),
  setTheme: (theme) => {
    try {
      localStorage.setItem("lcai-theme", theme);
    } catch { /* ignore */ }
    if (typeof document !== "undefined") {
      document.documentElement.setAttribute("data-theme", theme);
    }
    set({ theme });
  },
}));

export function applyTheme(theme: ThemeId) {
  if (typeof document !== "undefined") {
    document.documentElement.setAttribute("data-theme", theme);
  }
}
