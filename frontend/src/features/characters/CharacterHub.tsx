import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { api } from "../../api/client";
import { charactersApi } from "../../api/characters";
import type { Character } from "../../types";

interface ChatRow {
  id: string;
  title?: string | null;
  persona_display_name?: string;
  last_message_at?: string | null;
  created_at?: string | null;
}

export default function CharacterHub() {
  const { id } = useParams();
  const [character, setCharacter] = useState<Character | null>(null);
  const [chats, setChats] = useState<ChatRow[]>([]);

  useEffect(() => {
    if (!id) return;
    charactersApi.get(id).then(setCharacter).catch(console.error);
    api.get<ChatRow[]>(`/characters/${id}/chats`).then(setChats).catch(console.error);
  }, [id]);

  if (!character) {
    return <p className="text-slate-400 text-sm">Loading…</p>;
  }

  return (
    <div className="max-w-3xl space-y-6">
      <div className="flex items-start gap-4">
        <div className="w-20 h-20 rounded-2xl overflow-hidden bg-surface-800 shrink-0 border border-slate-700">
          {character.avatar_path ? (
            <img src={character.avatar_path} alt="" className="w-full h-full object-cover" />
          ) : (
            <div className="w-full h-full flex items-center justify-center text-2xl text-accent-muted">
              {character.name.charAt(0)}
            </div>
          )}
        </div>
        <div className="min-w-0 flex-1">
          <h1 className="text-2xl font-semibold truncate">{character.name}</h1>
          <p className="text-sm text-slate-400 line-clamp-2">
            {character.description || "No description"}
          </p>
          <p className="text-xs text-slate-500 mt-1">
            Filter: {character.filter_level || "mature"} · {chats.length} chat
            {chats.length === 1 ? "" : "s"}
          </p>
        </div>
      </div>

      <div className="flex flex-wrap gap-2">
        <Link
          to={`/chats/new?character=${character.id}`}
          className="btn btn-primary text-sm"
        >
          + New chat
        </Link>
        <Link to={`/characters/${character.id}/edit`} className="btn btn-ghost text-sm">
          Edit character
        </Link>
        <Link to="/characters" className="btn btn-ghost text-sm">
          All characters
        </Link>
      </div>

      <section className="space-y-2">
        <h2 className="font-medium">Saved chats</h2>
        <p className="text-xs text-slate-500">
          Multiple histories with the same character — like Character.AI. Start a new chat anytime
          without losing previous ones.
        </p>
        {chats.length === 0 && (
          <p className="text-sm text-slate-500">No chats yet. Start the first one.</p>
        )}
        {chats.map((c) => (
          <Link
            key={c.id}
            to={`/chats/${c.id}`}
            className="card block px-4 py-3 hover:border-accent/40 transition"
          >
            <div className="font-medium text-sm truncate">
              {c.title || `Chat with ${character.name}`}
            </div>
            <div className="text-xs text-slate-500 mt-0.5">
              as {c.persona_display_name || "you"}
              {c.last_message_at ? ` · ${c.last_message_at}` : ""}
            </div>
          </Link>
        ))}
      </section>
    </div>
  );
}
