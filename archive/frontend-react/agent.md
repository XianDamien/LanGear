# Langear Product Agent Notes (Design + FE/BE)

Purpose
- This file is a shared, concise spec for design and front/back-end alignment.
- It reflects the current PRD direction and prototype gaps.

Primary User Goal
- Improve spoken expression and retelling fluency + accuracy via repeated listening and speaking.

Core Flow (Web)
1) Login -> select language pair (en-zh, fr-zh, etc.). Dev can skip login.
2) Dashboard -> active decks, today tasks (user sets new/review counts), streak calendar, favorites.
3) Library -> nested structure (volume -> unit -> lesson). Choose lesson to start.
4) Study session (card loop)
   - Front: play original audio, record user retelling, show live ASR stream (no correctness).
   - Flip: immediate reveal (no delay).
   - Back: original text + audio, user audio + transcript, word highlights (noun phrases highlighted, verbs underlined),
     dictionary/AI explanation on word click, note field, FSRS self-grade.
   - AI feedback runs async after flip.
5) Lesson end -> prompt for AI summary report (async).

AI Modules (Async)
- Live ASR stream for front (low-cost model, no correctness judgment).
- Single-sentence feedback: upload original audio + user audio (+ transcript). Store results.
- Lesson summary: aggregate single-sentence feedback into a report.
- Translation is NOT shown by default. User can tap to request translation (filled asynchronously).

Design Notes
- Card-based flow (front/back).
- Back side prioritizes compare: original vs user (audio + text).
- Dictionary/AI explanation should be lightweight and non-blocking.
- Summary prompt is a modal at lesson end.

Data / Storage (Demo)
- Use local storage for progress, feedback, summary, notes (dev demo).
- Keep data model ready for later API wiring.

Out of Scope (Now)
- Community, points, full login system (P2).
- Custom import is lower priority (P2) but should be planned.

Open Items (TBD)
- Final AI feedback schema.
- Exact summary trigger threshold (default: end of lesson/min deck unit).

