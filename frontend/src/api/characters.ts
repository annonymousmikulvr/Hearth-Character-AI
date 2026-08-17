import { api } from "./client";
import type { Character, CharacterListItem } from "../types";

export const charactersApi = {
  list: (params?: { search?: string; include_archived?: boolean }) => {
    const q = new URLSearchParams();
    if (params?.search) q.set("search", params.search);
    if (params?.include_archived) q.set("include_archived", "true");
    const qs = q.toString();
    return api.get<CharacterListItem[]>(`/characters${qs ? `?${qs}` : ""}`);
  },
  get: (id: string) => api.get<Character>(`/characters/${id}`),
  create: (data: Partial<Character>) => api.post<Character>("/characters", data),
  update: (id: string, data: Partial<Character>) =>
    api.patch<Character>(`/characters/${id}`, data),
  remove: (id: string, hard = false) =>
    api.delete<{ message: string }>(`/characters/${id}?hard=${hard}`),
};
