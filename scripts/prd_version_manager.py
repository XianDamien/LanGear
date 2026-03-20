#!/usr/bin/env python3
"""Manage a single PRD mirror and archived snapshots."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parent.parent
TRACKING_ROOT = REPO_ROOT / "docs" / "prd_versions"
SOURCE_FILE = REPO_ROOT / "PRD.md"
CURRENT_FILE = TRACKING_ROOT / "current.md"
ARCHIVE_DIR = TRACKING_ROOT / "archived"
METADATA_FILE = TRACKING_ROOT / "metadata.json"


def iso_now() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def default_metadata() -> dict[str, Any]:
    return {
        "name": "prd",
        "version": None,
        "description": "LanGear PRD version tracking",
        "owner": "pm@lan",
        "updated_at": iso_now(),
        "tags": ["prd", "version-tracking"],
        "notes": "Authoring source remains PRD.md. current.md is the synced mirror; archived/ stores release snapshots.",
        "files": {
            "source": str(SOURCE_FILE.relative_to(REPO_ROOT)),
            "current": str(CURRENT_FILE.relative_to(REPO_ROOT)),
            "archived_dir": str(ARCHIVE_DIR.relative_to(REPO_ROOT)),
        },
        "current_state": {
            "source_sha256": None,
            "current_sha256": None,
            "in_sync": False,
        },
        "current_snapshot": None,
        "changelog": [],
    }


def ensure_scaffold() -> None:
    TRACKING_ROOT.mkdir(parents=True, exist_ok=True)
    ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)
    if not METADATA_FILE.exists():
        write_json(METADATA_FILE, default_metadata())


def sync() -> dict[str, Any]:
    ensure_scaffold()
    metadata = read_json(METADATA_FILE) or default_metadata()

    if not SOURCE_FILE.exists():
        raise FileNotFoundError(f"Source file not found: {SOURCE_FILE}")

    shutil.copyfile(SOURCE_FILE, CURRENT_FILE)
    source_sha = file_sha256(SOURCE_FILE)
    current_sha = file_sha256(CURRENT_FILE)

    metadata["updated_at"] = iso_now()
    metadata["files"] = {
        "source": str(SOURCE_FILE.relative_to(REPO_ROOT)),
        "current": str(CURRENT_FILE.relative_to(REPO_ROOT)),
        "archived_dir": str(ARCHIVE_DIR.relative_to(REPO_ROOT)),
    }
    metadata["current_state"] = {
        "source_sha256": source_sha,
        "current_sha256": current_sha,
        "in_sync": source_sha == current_sha,
    }
    write_json(METADATA_FILE, metadata)
    return metadata


def snapshot(version: str, date: str, changes: str) -> Path:
    metadata = sync()

    archive_path = ARCHIVE_DIR / f"PRD_{version}_{date}.md"
    shutil.copyfile(SOURCE_FILE, archive_path)
    archive_sha = file_sha256(archive_path)

    metadata["version"] = version
    metadata["updated_at"] = iso_now()
    metadata["current_snapshot"] = {
        "version": version,
        "date": date,
        "file": str(archive_path.relative_to(REPO_ROOT)),
        "sha256": archive_sha,
    }

    changelog = metadata.setdefault("changelog", [])
    existing_index = next(
        (
            index
            for index, entry in enumerate(changelog)
            if entry.get("version") == version and entry.get("date") == date
        ),
        None,
    )
    changelog_entry = {
        "version": version,
        "date": date,
        "changes": changes,
        "file": str(archive_path.relative_to(REPO_ROOT)),
    }
    if existing_index is None:
        changelog.insert(0, changelog_entry)
    else:
        changelog[existing_index] = changelog_entry

    write_json(METADATA_FILE, metadata)
    return archive_path


def status() -> int:
    ensure_scaffold()
    metadata = read_json(METADATA_FILE) or default_metadata()

    source_exists = SOURCE_FILE.exists()
    current_exists = CURRENT_FILE.exists()
    source_sha = file_sha256(SOURCE_FILE) if source_exists else None
    current_sha = file_sha256(CURRENT_FILE) if current_exists else None
    in_sync = bool(source_sha and current_sha and source_sha == current_sha)

    print(
        "\n".join(
            [
                "[prd]",
                f"  source:  {SOURCE_FILE.relative_to(REPO_ROOT)}",
                f"  current: {CURRENT_FILE.relative_to(REPO_ROOT)}",
                f"  version: {metadata.get('version') or 'unset'}",
                f"  in_sync: {in_sync}",
                f"  snapshot: {(metadata.get('current_snapshot') or {}).get('file', 'none')}",
            ]
        )
    )
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Manage LanGear PRD mirror and snapshots.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("status", help="Show PRD sync and snapshot status.")
    subparsers.add_parser("sync", help="Sync PRD.md into docs/prd_versions/current.md.")

    snapshot_parser = subparsers.add_parser("snapshot", help="Create an archived PRD snapshot.")
    snapshot_parser.add_argument("--version", required=True, help="Version label, e.g. v2.2")
    snapshot_parser.add_argument("--date", required=True, help="Snapshot date, e.g. 2026-03-20")
    snapshot_parser.add_argument("--changes", required=True, help="Short changelog summary")

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "status":
        return status()

    if args.command == "sync":
        sync()
        print("Synced prd")
        return 0

    if args.command == "snapshot":
        archive_path = snapshot(
            version=args.version,
            date=args.date,
            changes=args.changes,
        )
        print(f"Created snapshot: {archive_path.relative_to(REPO_ROOT)}")
        return 0

    parser.error("Unknown command")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
