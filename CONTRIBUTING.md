# Contributing to Hearth

Thanks for helping improve a local-first character platform.

## Ground rules

- Keep the app **local-first**: no required cloud AI, accounts, or telemetry.
- Prefer small, reviewable pull requests.
- Do not break existing SQLite data without a migration + `schema_ensure` fallback.
- UI copy should stay clear for non-developers (labels, examples, min/max hints).

## Dev setup

1. Follow the README quick start.
2. Backend: `backend/.venv` + `python run.py`
3. Frontend: `npm run dev` in `frontend/`
4. Point the UI at a disposable data folder while testing migrations.

## Code style

- **Backend:** Python 3.11+, FastAPI, type hints where practical, async SQLite via aiosqlite.
- **Frontend:** React + TypeScript + Tailwind; shared `FormField` for forms.
- Avoid large silent refactors of prompt/compiler paths unless the PR is about that area.

## Migrations

1. Add `backend/migrations/NNN_name.sql`
2. Extend `backend/app/schema_ensure.py` so existing installs self-heal
3. Document any user-visible behavior change in the PR description

## Testing checklist (manual)

- [ ] Fresh setup wizard creates a database
- [ ] Create persona + character + standard chat
- [ ] Send / regenerate / continue / hint
- [ ] `/help` and one public command
- [ ] Settings: Ollama connection
- [ ] Restart backend; old chats still open

## Issues

Please include OS, Python/Node versions, model name, and the backend traceback when reporting bugs.
