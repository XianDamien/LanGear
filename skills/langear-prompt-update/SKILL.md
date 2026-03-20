---
name: langear-prompt-update
description: Update LanGear's Gemini prompt assets safely and consistently. Use this skill whenever the user asks to modify `backend/app/adapters/prompts/**`, tune `single_feedback.txt` or `lesson_summary.txt`, change feedback JSON shape, bump `GEMINI_PROMPT_VERSION`, revise prompt wording, or align prompt output with frontend/backend contracts or PRD requirements. Also use it when the user mentions "prompt优化", "改prompt", "更新提示词", "Gemini prompt", or any request to change AI feedback behavior in LanGear.
---

# LanGear Prompt Update

## Intent
Change LanGear prompt files in a way that preserves contract stability, keeps prompt versions traceable, and avoids silent mismatches between prompt output, backend normalization, frontend rendering, and PRD expectations.

## Project Scope
This skill is specific to LanGear's Gemini prompt layer:

- `backend/app/adapters/prompts/<version>/single_feedback.txt`
- `backend/app/adapters/prompts/<version>/lesson_summary.txt`
- `backend/app/adapters/prompts/README.md`
- `backend/app/adapters/gemini_adapter.py`
- `backend/app/config.py` (`gemini_prompt_version`)

Prompt changes often affect:

- `PRD.md`
- `PRD_BASELINE.md`
- frontend feedback rendering
- backend JSON normalization and validation

## Use This Skill When
- user asks to change prompt wording or behavior
- user wants to add/remove fields in Gemini output JSON
- user wants better `issues[]`, `suggestions[]`, timestamps, or summary quality
- user wants to create `v2` from `v1`
- user wants prompt changes aligned with a new PRD or frontend contract
- user reports "模型输出格式不稳定", "timestamp 不对", "issues 不够具体", or similar prompt-quality issues

## Core Rules
1. Read the current prompt files and the adapter before editing anything.
2. Treat prompt output schema as an API contract, not casual prose.
3. If behavior or output shape changes materially, create a new prompt version folder instead of silently mutating the old version.
4. Keep `single_feedback.txt` and `lesson_summary.txt` in the same prompt version unless there is a strong reason not to.
5. If prompt output requirements change, check whether `gemini_adapter.py`, PRD, or frontend types also need updates.
6. Do not add fallback schemas or relaxed parsing branches unless the user explicitly wants them.
7. Keep prompts concise and operational; avoid bloating them with duplicated rules already enforced in code.

## Default Workflow

### Step 1: Inspect Current State
Read:

- `backend/app/adapters/prompts/README.md`
- active version folder from `backend/app/config.py`
- `backend/app/adapters/gemini_adapter.py`
- relevant PRD sections if the request changes output contract or product behavior

Confirm:

- active prompt version
- current JSON schema expected by backend
- whether frontend consumes the changed fields

### Step 2: Decide Edit In Place vs New Version
Use this rule:

- Edit in place only for typo fixes, wording clarifications, or non-behavioral cleanup.
- Create a new version folder for any of:
  - output field additions/removals/renames
  - stronger or weaker behavioral requirements
  - timestamp policy changes
  - summary structure changes
  - changes likely to affect evaluation quality materially

Default new-version flow:

```bash
cp -R backend/app/adapters/prompts/v1 backend/app/adapters/prompts/v2
```

Then edit files under the new folder and update the prompt README.

### Step 3: Update Prompt Content
When editing prompt files:

- keep the system intent explicit
- separate task, output schema, and rules
- define maximum list sizes if backend/UI assumes bounded output
- state timestamp semantics precisely if timestamps are requested
- use `null` handling rules explicitly when a field is optional

For `single_feedback.txt`, make sure the prompt stays aligned with backend normalization:

- `pronunciation`
- `completeness`
- `fluency`
- `suggestions[]`
- `issues[]`

For `lesson_summary.txt`, keep it aligned with summary output:

- `overall`
- `patterns[]`
- `prioritized_actions[]`

### Step 4: Update Activation Path
If a new prompt version is created:

- update `backend/app/adapters/prompts/README.md`
- update `GEMINI_PROMPT_VERSION` in `backend/.env` only if the user asked to activate it now
- otherwise leave runtime config unchanged and say the new version is staged but inactive

Never silently switch the active prompt version without making that explicit.

### Step 5: Check Downstream Contract Impact
If prompt output shape or semantics changed, inspect and update as needed:

- `backend/app/adapters/gemini_adapter.py`
- frontend feedback types and rendering
- `PRD.md`
- `PRD_BASELINE.md`

Typical examples:

- if `issues[]` shape changes, update normalization and PRD
- if summary structure changes, update summary types and PRD
- if timestamps become optional/required, update prompt text and contract docs together

### Step 6: Validate
At minimum, verify:

- prompt files exist at the expected version path
- adapter still points to a real version folder
- JSON schema in prompt matches backend parser expectations
- any documented command or version reference is still correct

If code changed, run the smallest relevant verification command.

## Output Template
When finishing, report:

1. which prompt version was edited or created
2. whether it is active now or only staged
3. whether schema/contract changed
4. which code/docs were updated to keep alignment
5. any follow-up risk, such as "needs real prompt eval with sample audio"

## Examples

**Example 1:**
Input: "把 single_feedback 的 issues 改得更具体，并且如果时间戳拿不准允许 null"
Expected handling:
- inspect `single_feedback.txt` and `gemini_adapter.py`
- likely edit prompt behavior and possibly keep schema unchanged
- if change is material, create a new prompt version folder
- sync PRD only if contract wording changes

**Example 2:**
Input: "新增一个 summary 字段叫 coach_note"
Expected handling:
- treat as schema change
- create a new prompt version
- update backend parsing and any summary consumers
- update PRD docs

**Example 3:**
Input: "只改一下 prompt 文案，让 suggestions 更短一点"
Expected handling:
- inspect current prompt
- edit in place if truly non-breaking
- no runtime version bump unless asked

## Notes
- This skill is about safe prompt evolution, not generic prompt engineering advice.
- Prefer minimal diffs, but do not preserve a broken contract just to keep the diff small.
- If the user only wants brainstorming, still use this skill to frame the impact on versioning and contracts.
