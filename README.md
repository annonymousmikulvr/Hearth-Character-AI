# Hearth

**Local-first AI character roleplay** — Character.AI / CHAI-style chats that run on **your** hardware.

No cloud AI account. No mandatory login. No conversation telemetry.  
Characters, personas, worlds, memories, and chat history live in a SQLite database on disk you choose.

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-green.svg)](https://www.python.org/downloads/)
[![Node 18+](https://img.shields.io/badge/node-18+-green.svg)](https://nodejs.org/)
[![Ollama](https://img.shields.io/badge/Ollama-local%20models-purple.svg)](https://ollama.com)

---

## Why Hearth?

| Goal | How Hearth approaches it |
|------|---------------------------|
| Privacy | All data on disk you choose; Ollama stays local |
| Control | Deep character/persona cards, worlds, filters, branches |
| Usability | One-click launchers, guided setup, field hints and examples |
| Roleplay | Markup (`*actions*` / dialogue lines), side characters, scenes |
| Power users | Slash commands, memory pins, intensity, custom UI packs |

---

## Features

### Core
- **Characters** — personality, greeting, filter level, family tree, side roster, triggers, mood board, response length
- **Personas** — who you are in chat, facts the model should remember, modes/age, family tree
- **Chats** — multiple histories per character, custom seed scripts, Continue, Hint suggestions
- **Worlds** — tone, rules, locations; Scene vs World message types
- **Memory graph** — scoped notes you can pin; mute topics per chat

### Chat quality
- Local **Ollama** complete-response generation (playback is separate)
- First-person voice guidance + post-process beat formatting
- Side-character separation (other people should not steal the main character's lines)
- Regen + soft / sharp / playful tone variants
- Ratings, pins, intensity slider, per-chat filter and model
- Public slash commands (`/help`, `/timeskip`, `/scene`, `/pin`, ...)

### App
- Themes + **custom UI packs** (import/export JSON)
- Generation speed profiles (Fast / Balanced / Quality)
- Export characters and personas
- Dev mode commands for testing memory / backstory / sides

---

## Requirements

| Tool | Version | Notes |
|------|---------|--------|
| [Python](https://www.python.org/downloads/) | **3.11+** | Backend API |
| [Node.js](https://nodejs.org/) | **18+** | Frontend (Vite) |
| [Ollama](https://ollama.com) | latest | **Recommended** for local models |

Optional: local Stable Diffusion / Automatic1111 for character images (not required).

**Hardware:** consumer PCs work. Smaller models (3B–8B) are fine for everyday use.

---

## Quick start

### Windows

1. Install **Python 3.11+** (enable *Add python.exe to PATH*)
2. Install **Node.js 18+** (LTS is fine)
3. Install **[Ollama](https://ollama.com)** and pull a model:

```bat
ollama pull llama3.2
```

4. Download / clone this repository
5. Double-click **`start.bat`**
6. Open **http://127.0.0.1:5173**
7. First-run wizard → choose a data folder (example: `C:\Users\You\HearthData`) → **Create database**

Leave the two console windows open while you use the app.

### macOS / Linux

```bash
# After installing Python 3.11+, Node 18+, and Ollama:
ollama pull llama3.2

git clone https://github.com/YOUR_USERNAME/hearth.git
cd hearth
chmod +x start.sh
./start.sh
```

Browser → **http://127.0.0.1:5173**

---

## Manual start (if the launcher fails)

**Terminal 1 — backend**

```bash
cd backend
python -m venv .venv

# Windows:
.venv\Scripts\activate
# macOS / Linux:
source .venv/bin/activate

pip install -r requirements.txt
python run.py
```

API: **http://127.0.0.1:8741**

**Terminal 2 — frontend**

```bash
cd frontend
npm install
npm run dev
```

UI: **http://127.0.0.1:5173** (Vite proxies `/api` to the backend)

---

## First 10 minutes

1. **Settings** — confirm Ollama is connected; pick a default model  
2. **Personas** — create *you* (name + a few facts)  
3. **Characters** — create someone to talk to (name, personality, greeting)  
4. **Chats → New** — pick character + persona → Start  
5. Use **Hint** if stuck, **Continue** if you want the bot to keep going alone  
6. Type `/help` in the chat box for commands  

**Custom opening:** New chat → **Custom** → optional situation → **Auto-generate chat preset** → edit → Start.

Roleplay markup example:

```text
*I cross my arms.*
— "You're late."
```

---

## Slash commands (everyone)

| Command | Description |
|---------|-------------|
| `/help` | List commands in-chat |
| `/timeskip [text]` | Scene time-skip header |
| `/scene text` | Scene beat |
| `/world text` | World lore/rule beat |
| `/pin text` | Pin a beat the model should respect |
| `/mute topic` | Soft-avoid a topic |
| `/branch name` | Named timeline branch |
| `/intensity 0-100` | Emotional intensity |
| `/filter mature` | Per-chat content filter |
| `/continue` | Bot continues without a user line |
| `/hint` | Suggest user replies |
| `/as Name line` | Inject a side-character line |
| `/age 19` or `/age +1` | Temporary age (this chat only) |
| `/clothes ...` | Temporary outfit (this chat only) |

Full list: [docs/COMMANDS.md](docs/COMMANDS.md) · detailed setup: [docs/SETUP.md](docs/SETUP.md)

---

## Project layout

```text
hearth/
├── backend/           # FastAPI + SQLite + Ollama client
│   ├── app/
│   ├── migrations/
│   └── run.py
├── frontend/          # React + Vite + Tailwind
├── docs/              # Setup & commands
├── start.bat          # Windows one-click
├── start.sh           # macOS / Linux one-click
├── LICENSE            # MIT
└── README.md
```

Application data (database, avatars, exports) is **outside** the repo — path chosen at first run.

---

## Privacy

- No required cloud AI  
- No required account  
- No cloud chat/memory storage by Hearth  
- Inference targets **your** Ollama instance (typically `127.0.0.1`)  
- Optional image backends are local URLs you configure  

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| UI works, chat fails | Keep backend window open; open http://127.0.0.1:8741/api/health |
| Model errors | `ollama list` then `ollama pull ...`; set model in Settings |
| Port already in use | Close old Hearth consoles |
| Schema / missing column errors | Restart backend after updates (auto-migrate on startup) |
| Odd roleplay format | Stronger model + Regenerate; try Balanced/Quality speed |
| Side character mixed into main | Name them clearly; `/as` or roster; Regenerate after intro |

---

## Contributing

Issues and pull requests are welcome. See [CONTRIBUTING.md](CONTRIBUTING.md).

Security notes: [SECURITY.md](SECURITY.md).

---

## License

[MIT](LICENSE) — use, modify, and share freely. Attribution is appreciated but not required.

---

## Disclaimer

Hearth runs **local** language models. Quality depends on the model you choose. Content filters are under your control; you are responsible for how you use the software.
