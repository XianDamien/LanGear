---
name: langear-fullstack-investigation
description: Investigate LanGear full-stack behavior by reading the local Vue frontend and the production FastAPI backend via ssh langear-prod at /srv/langear. Use for LanGear logic reviews, frontend/backend contract checks, recording, realtime ASR, OSS upload, Gemini feedback, FSRS scheduling, dashboard, settings, deployment and log investigation, and Chinese requests like 看前后端逻辑, 排查后端, 生产后端, 录音上传, 实时转写, AI 评测.
---

# LanGear Fullstack Investigation

## Purpose

Use this skill to understand or debug LanGear across the local frontend and the production backend. It keeps the investigation anchored to the deployed backend code instead of assuming the local backend is current.

## Source Rules

- Read frontend code from the current local repository, mainly `frontend/src`.
- Read backend code from production with `ssh langear-prod` under `/srv/langear`.
- Treat `/srv/langear/backend/app` as the backend source of truth for logic investigations unless the user explicitly asks about local backend changes.
- Do not print or read secret values from `backend/.env`, `frontend/.env`, `.postgres.env`, or similar files unless the user explicitly asks and there is a safe reason.
- Production `/srv/langear` may not be a git worktree. Do git operations in the local repo unless the user explicitly asks for remote deployment work.
- For research or bug diagnosis, report the likely file and location first. Do not edit code until the user clearly asks to change it.

## Default Workflow

1. Identify the user-visible symptom or the product flow being reviewed.
2. Inspect local frontend entry points with `rg` before opening files.
3. Inspect the production backend over SSH, selecting routers, services, tasks, adapters, and repositories related to the flow.
4. Map the frontend/backend contract, including request payloads, response envelope unwrapping, status values, and error codes.
5. State the current logic and any suspected issue with concrete file paths.
6. If changes are requested, keep them task-scoped and verify with the smallest relevant frontend or backend command.

## High-Value Files

Frontend:

- `frontend/src/router/index.ts`
- `frontend/src/services/http.ts`
- `frontend/src/services/api/study.ts`
- `frontend/src/types/api.ts`
- `frontend/src/views/StudySessionView.vue`
- `frontend/src/stores/study.ts`
- `frontend/src/stores/studyTasks.ts`
- `frontend/src/composables/useRealtimeAsr.ts`
- `frontend/src/composables/useRecorder.ts`
- `frontend/src/stores/dashboard.ts`
- `frontend/src/services/api/decks.ts`

Production backend:

- `/srv/langear/backend/app/main.py`
- `/srv/langear/backend/app/config.py`
- `/srv/langear/backend/app/routers/study.py`
- `/srv/langear/backend/app/routers/realtime.py`
- `/srv/langear/backend/app/routers/oss.py`
- `/srv/langear/backend/app/routers/decks.py`
- `/srv/langear/backend/app/services/review_service.py`
- `/srv/langear/backend/app/services/realtime_session_service.py`
- `/srv/langear/backend/app/services/study_session_service.py`
- `/srv/langear/backend/app/services/content_service.py`
- `/srv/langear/backend/app/tasks/review_task.py`
- `/srv/langear/backend/app/adapters/gemini_adapter.py`
- `/srv/langear/backend/app/adapters/realtime_asr_adapter.py`
- `/srv/langear/backend/app/adapters/oss_adapter.py`

## Core Contracts

- Frontend HTTP base defaults to `/api/v1`; `frontend/src/services/http.ts` unwraps backend `{ request_id, data }` responses into `response.data`.
- Study submission uses `POST /study/submissions` after the frontend has an OSS path and a ready realtime ASR session id.
- The production backend validates card, lesson, OSS recordings prefix, realtime session existence, lesson/card match, and realtime final transcript readiness before creating a `review_log`.
- The backend processes AI feedback asynchronously in a daemon thread via `process_review_task`, then the frontend polls `GET /study/submissions/{submission_id}`.
- Rating is decoupled from AI feedback. `POST /study/submissions/{submission_id}/rating` updates FSRS only after feedback has been created.
- Realtime ASR session state is process-local in memory with TTL cleanup. Backend instance/process affinity matters when debugging session-not-found errors.
- Gemini feedback uses the official `google-genai` SDK with dual audio input: reference audio and user audio are downloaded from signed OSS URLs and sent inline.

## Production Commands

Use targeted SSH commands instead of copying whole trees:

```bash
ssh langear-prod 'cd /srv/langear && sed -n "1,260p" backend/app/routers/study.py'
ssh langear-prod 'cd /srv/langear && sed -n "1,360p" backend/app/services/review_service.py'
ssh langear-prod 'cd /srv/langear && docker compose -f docker-compose.yml -f docker-compose.server.yml logs --tail=200 backend'
```

For local verification:

```bash
cd frontend && pnpm typecheck
cd frontend && pnpm build
cd backend && uv run pytest
```

## Deeper Reference

Read `references/architecture.md` when the task needs a fuller map of the current frontend/backend flow, error surfaces, and investigation checklist.
