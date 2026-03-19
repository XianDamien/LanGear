# Prompt Versioning

Prompt templates are versioned by folder name.

## Structure

- `v1/single_feedback.txt`
- `v1/lesson_summary.txt`

## How to create a new version

1. Copy the current version directory, for example `v1` to `v2`.
2. Edit prompt files in `v2`.
3. Update `GEMINI_PROMPT_VERSION=v2` in backend config to activate it.

Git history tracks all prompt diffs between versions.
