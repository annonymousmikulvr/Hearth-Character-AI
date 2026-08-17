# Setup guide (detailed)

## Windows checklist

1. **Python 3.11+**
   - https://www.python.org/downloads/
   - Enable **Add python.exe to PATH**
   - Verify: `python --version`

2. **Node.js 18+**
   - https://nodejs.org/ (LTS)
   - Verify: `node --version` and `npm --version`

3. **Ollama**
   - https://ollama.com
   - `ollama pull llama3.2` (or another model you prefer)
   - Leave Ollama running

4. **Hearth**
   - Clone or unzip the repo
   - Double-click `start.bat`
   - Browser → http://127.0.0.1:5173
   - First-run: absolute data path, e.g. `C:\Users\YourName\HearthData`

## macOS checklist

```bash
brew install python@3.11 node
# Install Ollama app or brew formula
ollama pull llama3.2

git clone https://github.com/YOUR_USERNAME/hearth.git
cd hearth
chmod +x start.sh
./start.sh
```

## Linux checklist

```bash
sudo apt update
sudo apt install python3 python3-pip python3-venv nodejs npm
# Install Ollama from https://ollama.com/download/linux
ollama pull llama3.2

git clone https://github.com/YOUR_USERNAME/hearth.git
cd hearth
chmod +x start.sh
./start.sh
```

## Ports

| Service | Default |
|---------|---------|
| Frontend (Vite) | `5173` |
| Backend (FastAPI) | `8741` |

Firewall: allow localhost for these ports if a security tool blocks them.

## Updating

```bash
git pull
cd backend && .venv/bin/pip install -r requirements.txt   # or Windows venv path
cd ../frontend && npm install
```

Restart both processes. Migrations run when the backend starts.

## Choosing a model

| Goal | Example direction |
|------|-------------------|
| Faster / weaker GPU | 3B–7B instruct models |
| Better roleplay | 8B–14B if VRAM allows |
| Quality over speed | Settings → Generation speed → Quality |

Always set the **default model** in Hearth Settings after `ollama pull`.

## Data folder

Contains SQLite DB, avatars, and exports. Back it up like any other personal files.  
Deleting the repo does **not** delete the data folder unless you put data inside the repo (not recommended).
