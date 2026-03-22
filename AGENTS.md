# LanGear Agent Guide

## Project Summary

LanGear is an AI-assisted English retelling training app.

- Frontend: Vue 3 + TypeScript + Vite + Pinia
- Backend: FastAPI + SQLAlchemy + SQLite + Alembic
- ASR: DashScope `qwen3-asr-flash`
- AI feedback: Google Gemini via official `google-genai` SDK
- Storage: Aliyun OSS
- Scheduler: FSRS

## Repo Layout

```text
frontend/src/
  components/
  views/
  stores/
  services/
  composables/
  types/

backend/app/
  adapters/
  models/
  repositories/
  routers/
  services/
  tasks/
```

## Run Commands

- Frontend: `cd frontend && pnpm dev`
- Backend: `cd backend && uv run uvicorn app.main:app --reload`
- Backend tests: `cd backend && uv run pytest`

## Environment Rules

- Frontend env lives in `frontend/.env`
- Backend env lives in `backend/.env`
- Do not rely on repo root `.env` for backend runtime
- Do not hardcode API keys

## Integration Rules

- ASR must use `qwen3-asr-flash`
- Gemini must use the official SDK path only
- Do not use Gemini relay
- Do not add Gemini runtime fallback branches
- Backend Gemini config should come from `backend/.env`
- OSS user audio and reference audio are handled by backend adapters

## Product Flow

1. User enters study session and plays reference audio.
2. User records retelling and receives live ASR text.
3. Frontend uploads recording to OSS.
4. Frontend submits study record to backend.
5. Backend runs async processing: ASR, Gemini feedback, FSRS update.
6. Frontend polls submission status and renders feedback.

## Working Rules

- Prefer minimal, task-scoped changes
- Do not mix unrelated dirty files into a commit
- Add or update tests when behavior changes
- Prefer reading existing code before changing architecture
- Only create a subagent when its output will materially affect the current task
- After creating a subagent, wait for and evaluate its result before ending the task
- If a subagent is no longer needed, explicitly cancel or close it to avoid wasting tokens
- `CLAUDE.md` is a symlink to `AGENTS.md`; treat `AGENTS.md` as the single source of truth
- Do not edit `CLAUDE.md` and `AGENTS.md` as if they were separate documents
- After meaningful code, workflow, or constraint changes, update `README.md` in the same task
- After product flow, contract, state-model, or acceptance changes, update `PRD.md` and `PRD_BASELINE.md` in the same task
- If no doc update is needed, state that explicitly in the final response

## Commit Rules

- Commit messages must use concise Chinese
- The title must include the main change points
- Only commit task-related files unless explicitly asked otherwise

## Documentation Files

- `README.md` is the repository entry document for setup, run commands, and developer workflow
- `PRD.md` is the detailed product and implementation spec
- `PRD_BASELINE.md` is the current baseline contract for aligned delivery

## Key Files

- `PRD.md`
- `PRD_BASELINE.md`
- `CLAUDE.md`
- `backend/app/config.py`
- `backend/app/adapters/asr_adapter.py`
- `backend/app/adapters/gemini_adapter.py`
