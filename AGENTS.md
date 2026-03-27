# LanGear Agent Guide

## Subagent Constraint

- Spawn subagents only when their output will materially affect the task
- After spawning a subagent, do not finish or close out the task before its result returns and is evaluated, unless the user explicitly cancels the work
- Do not create subagents just for appearance of parallelism
- If a subagent is no longer needed, cancel or close it explicitly instead of letting it run pointlessly and waste tokens

## Worktree Documentation Policy

- In feature worktrees, keep changes code-scoped unless the user explicitly asks for documentation edits
- Do not update project `README.md`, `PRD.md`, or `PRD_BASELINE.md` as part of routine worktree implementation, because those edits create avoidable merge conflicts
- Defer documentation rewrites until the related functionality is complete and merged, then update docs once in a final pass
- When documentation is intentionally deferred under this rule, say so explicitly in the final response

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
- Follow the subagent constraint and worktree documentation policy above
- `CLAUDE.md` is a symlink to `AGENTS.md`; treat `AGENTS.md` as the single source of truth
- Do not edit `CLAUDE.md` and `AGENTS.md` as if they were separate documents

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
