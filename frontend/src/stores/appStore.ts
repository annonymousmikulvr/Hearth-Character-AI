import { create } from "zustand";
import type { Persona, CharacterListItem, PersonaListItem } from "../types";
import { settingsApi } from "../api/settings";
import { personasApi } from "../api/personas";
import { charactersApi } from "../api/characters";

interface AppState {
  defaultPersona: Persona | null;
  personas: PersonaListItem[];
  characters: CharacterListItem[];
  loading: boolean;
  error: string | null;

  loadDefaultPersona: () => Promise<void>;
  setDefaultPersona: (id: string | null) => Promise<void>;
  loadPersonas: (search?: string) => Promise<void>;
  loadCharacters: (search?: string) => Promise<void>;
}

export const useAppStore = create<AppState>((set, get) => ({
  defaultPersona: null,
  personas: [],
  characters: [],
  loading: false,
  error: null,

  loadDefaultPersona: async () => {
    try {
      const res = await settingsApi.getDefaultPersona();
      set({ defaultPersona: res.persona });
    } catch (e) {
      set({ error: String(e) });
    }
  },

  setDefaultPersona: async (id) => {
    await settingsApi.setDefaultPersona(id);
    await get().loadDefaultPersona();
  },

  loadPersonas: async (search) => {
    set({ loading: true, error: null });
    try {
      const list = await personasApi.list({ search });
      set({ personas: list, loading: false });
    } catch (e) {
      set({ error: String(e), loading: false });
    }
  },

  loadCharacters: async (search) => {
    set({ loading: true, error: null });
    try {
      const list = await charactersApi.list({ search });
      set({ characters: list, loading: false });
    } catch (e) {
      set({ error: String(e), loading: false });
    }
  },
}));
