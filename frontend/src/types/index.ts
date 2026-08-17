export interface PersonaListItem {
  id: string;
  profile_name: string;
  chat_name: string;
  avatar_path?: string | null;
  tags: string[];
  is_archived: boolean;
  updated_at?: string | null;
}

export interface Persona extends PersonaListItem {
  age?: number | null;
  pronouns?: string | null;
  height?: string | null;
  build?: string | null;
  hair?: string | null;
  eyes?: string | null;
  skin?: string | null;
  clothing?: string | null;
  appearance_description?: string | null;
  traits: string[];
  personality_description?: string | null;
  likes: string[];
  dislikes: string[];
  habits: string[];
  speaking_style?: string | null;
  biography?: string | null;
  occupation?: string | null;
  location?: string | null;
  additional_facts: string[];
  how_they_act?: string | null;
  how_they_respond?: string | null;
  custom_instructions?: string | null;
  example_dialogues: { user: string; persona: string }[];
  created_at?: string | null;
}

export interface CharacterListItem {
  id: string;
  name: string;
  description?: string | null;
  avatar_path?: string | null;
  tags: string[];
  is_archived: boolean;
  updated_at?: string | null;
}

export interface Character extends CharacterListItem {
  system_prompt?: string | null;
  baseline_personality?: string | null;
  scenario?: string | null;
  greeting?: string | null;
  example_dialogues: { role: string; content: string }[];
  temperature?: number | null;
  top_p?: number | null;
  repetition_penalty?: number | null;
  context_window?: number | null;
  max_tokens?: number | null;
  model_profile_id?: string | null;
  model_name?: string | null;
  side_character_enabled: boolean;
  side_character_instructions?: string | null;
  version: number;
  created_at?: string | null;
}

export interface SetupStatus {
  setup_completed: boolean;
  data_root?: string | null;
  database_path?: string | null;
  version: string;
}

export interface ConversationListItem {
  id: string;
  title?: string | null;
  character_id: string;
  character_name?: string | null;
  persona_id: string;
  persona_display_name: string;
  persona_profile_name?: string | null;
  is_archived: boolean;
  last_message_at?: string | null;
  updated_at?: string | null;
}

export interface Conversation extends ConversationListItem {
  world_id?: string | null;
  temperature?: number | null;
  top_p?: number | null;
  repetition_penalty?: number | null;
  max_tokens?: number | null;
  model_name?: string | null;
  created_at?: string | null;
}

export interface Message {
  id: string;
  conversation_id: string;
  role: string;
  speaker_type: string;
  speaker_id?: string | null;
  speaker_name: string;
  raw_content: string;
  content_format: string;
  parent_message_id?: string | null;
  variant_index: number;
  is_selected_variant: boolean;
  temperature?: number | null;
  max_tokens?: number | null;
  model_name?: string | null;
  token_count?: number | null;
  generation_ms?: number | null;
  created_at?: string | null;
}
