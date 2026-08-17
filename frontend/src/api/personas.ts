import { api } from "./client";
import type { Persona, PersonaListItem } from "../types";

export const personasApi = {
  list: (params?: { search?: string; include_archived?: boolean }) => {
    const q = new URLSearchParams();
    if (params?.search) q.set("search", params.search);
    if (params?.include_archived) q.set("include_archived", "true");
    const qs = q.toString();
    return api.get<PersonaListItem[]>(`/personas${qs ? `?${qs}` : ""}`);
  },
  get: (id: string) => api.get<Persona>(`/personas/${id}`),
  create: (data: Partial<Persona>) => api.post<Persona>("/personas", data),
  update: (id: string, data: Partial<Persona>) =>
    api.patch<Persona>(`/personas/${id}`, data),
  remove: (id: string, hard = false) =>
    api.delete<{ message: string }>(`/personas/${id}?hard=${hard}`),
};
