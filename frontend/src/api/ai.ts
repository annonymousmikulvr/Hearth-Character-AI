import { api } from "./client";

export interface AIConnection {
  provider: string;
  base_url: string;
  available: boolean;
  models: string[];
  default_model: string;
}

export interface AIConfigUpdate {
  ollama_base_url?: string;
  default_model?: string;
  default_temperature?: number;
  default_top_p?: number;
  default_repetition_penalty?: number;
  default_max_tokens?: number;
}

export const aiApi = {
  connection: () => api.get<AIConnection>("/ai/connection"),
  models: () => api.get<{ models: string[]; base_url: string }>("/ai/models"),
  config: (body: AIConfigUpdate) => api.post<{ ok: boolean }>("/ai/config", body),
  test: (body?: { model?: string; prompt?: string }) =>
    api.post<{
      content: string;
      model: string;
      duration_ms?: number;
      prompt_tokens?: number;
      completion_tokens?: number;
    }>("/ai/test", body || {}),
};
