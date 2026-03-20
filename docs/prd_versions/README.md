# PRD Version Tracking

This directory tracks one canonical PRD only.

## Source Of Truth

- `PRD.md`

`docs/prd_versions/current.md` is a managed mirror for inspection and archival, not a second authoring surface.

## Layout

```text
docs/prd_versions/
  README.md
  metadata.json
  current.md
  archived/
```

## Commands

```bash
python3 scripts/prd_version_manager.py status
python3 scripts/prd_version_manager.py sync
python3 scripts/prd_version_manager.py snapshot --version v2.2 --date 2026-03-20 --changes "..."
```

## Workflow

1. Edit `PRD.md`.
2. Run `sync` to refresh `current.md`.
3. Run `snapshot` when you want a named archived version.
4. Commit the PRD change together with metadata and archived snapshot updates.
