import { api } from "./client";
import type { Persona } from "../types";

export const settingsApi = {
  getAll: () => api.get<Record<string, string>>("/settings"),
  getDefaultPersona: () =>
    api.get<{ persona_id: string | null; persona: Persona | null }>(
      "/settings/default-persona/current"
    ),
  setDefaultPersona: (persona_id: string | null) =>
    api.put<{ persona_id: string | null }>("/settings/default-persona", {
      persona_id,
    }),
};
