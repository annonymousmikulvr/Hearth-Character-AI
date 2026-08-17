import { api } from "./client";
import type { Conversation, ConversationListItem, Message } from "../types";

export interface ConversationCreatePayload {
  character_id: string;
  persona_id: string;
  persona_display_name?: string;
  title?: string;
  temperature?: number;
  top_p?: number;
  max_tokens?: number;
  model_name?: string;
  seed_notes?: string;
  is_custom?: boolean;
  world_id?: string;
  seed_messages?: { role: string; content: string }[];
}

export const conversationsApi = {
  list: (params?: { character_id?: string; include_archived?: boolean }) => {
    const q = new URLSearchParams();
    if (params?.character_id) q.set("character_id", params.character_id);
    if (params?.include_archived) q.set("include_archived", "true");
    const qs = q.toString();
    return api.get<ConversationListItem[]>(
      `/conversations${qs ? `?${qs}` : ""}`
    );
  },
  get: (id: string) => api.get<Conversation>(`/conversations/${id}`),
  create: (data: ConversationCreatePayload) =>
    api.post<Conversation>("/conversations", data),
  update: (id: string, data: Partial<Conversation>) =>
    api.patch<Conversation>(`/conversations/${id}`, data),
  remove: (id: string, hard = false) =>
    api.delete<{ message: string }>(`/conversations/${id}?hard=${hard}`),
  listMessages: (conversationId: string) =>
    api.get<Message[]>(`/conversations/${conversationId}/messages`),
  postMessage: (
    conversationId: string,
    body: { role?: string; raw_content: string; content_format?: string }
  ) =>
    api.post<Message>(`/conversations/${conversationId}/messages`, {
      role: body.role || "user",
      raw_content: body.raw_content,
      content_format: body.content_format || "markup",
    }),
  generate: (conversationId: string) =>
    api.post<{ messages: Message[]; state: string }>(
      `/conversations/${conversationId}/generate`,
      {}
    ),
  regenerate: (conversationId: string, messageId: string) =>
    api.post<{ messages: Message[]; state: string }>(
      `/conversations/${conversationId}/messages/${messageId}/regenerate`,
      {}
    ),
  listVariants: (conversationId: string, messageId: string) =>
    api.get<Message[]>(
      `/conversations/${conversationId}/messages/${messageId}/variants`
    ),
  selectVariant: (conversationId: string, messageId: string) =>
    api.post<Message>(
      `/conversations/${conversationId}/messages/${messageId}/select`,
      {}
    ),
  editMessage: (
    conversationId: string,
    messageId: string,
    raw_content: string
  ) =>
    api.patch<Message>(
      `/conversations/${conversationId}/messages/${messageId}`,
      { raw_content }
    ),
  deleteMessage: (conversationId: string, messageId: string) =>
    api.delete<{ message: string }>(
      `/conversations/${conversationId}/messages/${messageId}`
    ),
  rewind: (conversationId: string, messageId: string, includeMessage = true) =>
    api.post<{ message: string }>(
      `/conversations/${conversationId}/messages/${messageId}/rewind`,
      { include_message: includeMessage }
    ),
};
