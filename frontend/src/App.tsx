import { Routes, Route, NavLink, Navigate } from "react-router-dom";
import { useEffect, useState } from "react";
import { setupApi } from "./api/setup";
import type { SetupStatus } from "./types";
import SetupWizard from "./pages/SetupWizard";
import CharacterBrowser from "./features/characters/CharacterBrowser";
import CharacterEditor from "./features/characters/CharacterEditor";
import CharacterHub from "./features/characters/CharacterHub";
import PersonaBrowser from "./features/personas/PersonaBrowser";
import PersonaEditor from "./features/personas/PersonaEditor";
import ChatCreate from "./features/chats/ChatCreate";
import ConversationList from "./features/chats/ConversationList";
import ChatView from "./features/chats/ChatView";
import SettingsPage from "./pages/SettingsPage";
import CustomUiPage from "./pages/CustomUiPage";
import WorldBrowser from "./features/worlds/WorldBrowser";
import WorldEditor from "./features/worlds/WorldEditor";
import MemoryBrowser from "./features/memory/MemoryBrowser";
import { useThemeStore, applyTheme } from "./stores/themeStore";
import { applyStoredUiPack } from "./stores/uiPackStore";
import StatusBanner from "./components/StatusBanner";

function Shell({ children }: { children: React.ReactNode }) {
  const linkClass = ({ isActive }: { isActive: boolean }) =>
    `px-3 py-2 rounded-lg text-sm font-medium transition ${
      isActive
        ? "bg-accent text-white shadow-md"
        : "text-slate-400 hover:bg-surface-800 hover:text-white"
    }`;

  return (
    <div className="min-h-screen flex flex-col bg-surface-950">
      <header className="border-b border-slate-800 bg-surface-900/80 backdrop-blur-xl sticky top-0 z-20">
        <div className="max-w-7xl mx-auto px-3 h-12 flex items-center gap-2">
          <div className="flex items-center gap-2 mr-1 shrink-0">
            <div className="w-7 h-7 rounded-lg bg-gradient-to-br from-[var(--accent)] to-[var(--accent-hover)] shadow-lg" />
            <span className="font-semibold tracking-tight hidden md:inline text-sm">
              Hearth
            </span>
            <span className="text-[10px] text-slate-500 hidden lg:inline tracking-wide uppercase">
              local
            </span>
          </div>
          <nav className="flex gap-0.5 flex-1 overflow-x-auto">
            <NavLink to="/chats" className={linkClass}>Chats</NavLink>
            <NavLink to="/characters" className={linkClass}>Characters</NavLink>
            <NavLink to="/personas" className={linkClass}>Personas</NavLink>
            <NavLink to="/worlds" className={linkClass}>Worlds</NavLink>
            <NavLink to="/memories" className={linkClass}>Memory</NavLink>
            <NavLink to="/ui" className={linkClass}>UI</NavLink>
            <NavLink to="/settings" className={linkClass}>Settings</NavLink>
          </nav>
          <NavLink
            to="/chats/new"
            className="shrink-0 px-3 py-1.5 rounded-lg text-sm font-medium"
            style={{ background: "color-mix(in srgb, var(--accent) 18%, transparent)", color: "var(--accent-muted)" }}
          >
            + New Chat
          </NavLink>
        </div>
      </header>
      <main className="flex-1 max-w-7xl w-full mx-auto px-3 py-3"><StatusBanner />
        {children}</main>
    </div>
  );
}

export default function App() {
  const [setup, setSetup] = useState<SetupStatus | null>(null);
  const [checking, setChecking] = useState(true);
  const theme = useThemeStore((s) => s.theme);

  useEffect(() => {
    applyTheme(theme);
    applyStoredUiPack();
    try {
      const a = localStorage.getItem("lcai-custom-accent");
      const b = localStorage.getItem("lcai-custom-bg");
      if (a) {
        document.documentElement.style.setProperty("--accent", a);
        document.documentElement.style.setProperty("--accent-hover", a);
        document.documentElement.style.setProperty("--accent-muted", a);
      }
      if (b) document.documentElement.style.setProperty("--bg", b);
    } catch { /* ignore */ }
  }, [theme]);

  useEffect(() => {
    setupApi
      .status()
      .then(setSetup)
      .catch(() => setSetup({ setup_completed: false, version: "0.3.0" }))
      .finally(() => setChecking(false));
  }, []);

  if (checking) {
    return (
      <div className="min-h-screen flex items-center justify-center text-slate-400 bg-surface-950">
        <div className="w-10 h-10 rounded-xl animate-pulse" style={{ background: "var(--accent)" }} />
      </div>
    );
  }

  if (!setup?.setup_completed) {
    return <SetupWizard onComplete={(s) => setSetup(s)} />;
  }

  return (
    <Shell>
      <Routes>
        <Route path="/" element={<Navigate to="/chats" replace />} />
        <Route path="/characters" element={<CharacterBrowser />} />
        <Route path="/characters/new" element={<CharacterEditor />} />
        <Route path="/characters/:id" element={<CharacterHub />} />
        <Route path="/characters/:id/edit" element={<CharacterEditor />} />
        <Route path="/personas" element={<PersonaBrowser />} />
        <Route path="/personas/new" element={<PersonaEditor />} />
        <Route path="/personas/:id" element={<PersonaEditor />} />
        <Route path="/worlds" element={<WorldBrowser />} />
        <Route path="/worlds/:id" element={<WorldEditor />} />
        <Route path="/memories" element={<MemoryBrowser />} />
        <Route path="/chats" element={<ConversationList />} />
        <Route path="/chats/new" element={<ChatCreate />} />
        <Route path="/chats/:id" element={<ChatView />} />
        <Route path="/ui" element={<CustomUiPage />} />
        <Route path="/settings" element={<SettingsPage />} />
      </Routes>
    </Shell>
  );
}
