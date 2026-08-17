# Publishing Hearth on GitHub (open source)

This short guide is for maintainers putting Hearth on GitHub for the first time.

## 1. Create the repository

1. Sign in at [https://github.com](https://github.com)
2. **New repository**
3. Name: e.g. `hearth` or `local-character-ai`
4. Description: `Local-first AI character roleplay (Ollama + FastAPI + React)`
5. Public (for open source)
6. **Do not** add a README/license on GitHub if you already have them in this folder
7. Create

## 2. Push this project

In a terminal, from the project root (the folder that contains `README.md` and `backend/`):

```bash
git init
git add .
git commit -m "Initial release: Hearth local character AI"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO.git
git push -u origin main
```

Replace `YOUR_USERNAME` and `YOUR_REPO` with your GitHub values.

### Windows (GitHub Desktop)

1. Install [GitHub Desktop](https://desktop.github.com/)
2. File → Add Local Repository → select this folder
3. Publish repository → Public → Publish

## 3. MIT license (already included)

This project ships with an **MIT** `LICENSE` file. That is enough for open source on GitHub.  
GitHub will detect the license automatically after you push.

Optional: Repo → About → gear icon → check **MIT License**.

## 4. Nice extras on the repo page

- **About** description + topics: `ai`, `roleplay`, `ollama`, `local-first`, `fastapi`, `react`
- Enable **Issues** and **Discussions** if you want community help
- Add a screenshot later under a `docs/images/` folder and link it in the README

## 5. Releases (optional)

1. Tag a version: `git tag v0.4.0 && git push --tags`
2. GitHub → Releases → Draft a release from the tag
3. Attach a zip of the source if you want “download without git”

## 6. What “open source” means here

- Source code is public under MIT
- Anyone may use, modify, and redistribute
- You are **not** required to accept every pull request
- You remain responsible for what you publish; users remain responsible for how they run local models

## 7. Privacy note for the README

Hearth is designed not to require cloud AI. If you later add optional cloud providers, document them clearly so users can stay fully local.
