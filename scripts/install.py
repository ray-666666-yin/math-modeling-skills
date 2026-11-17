#!/usr/bin/env python3
"""Install/update this collection without deleting other skills or old versions."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from skill_common import (
    REPO_ROOT,
    SKILL_NAMES,
    SafetyError,
    absolute_path,
    assert_plain_path,
    exists,
    frontmatter,
    tree_digest,
)


@dataclass
class Plan:
    name: str
    source: Path
    target: Path
    action: str
    source_digest: dict[str, str]
    previous_digest: dict[str, str] | None


def default_destination() -> Path:
    codex_home = os.environ.get("CODEX_HOME")
    if codex_home:
        return absolute_path(codex_home) / "skills"
    return absolute_path(Path.home() / ".codex" / "skills")


def is_within(path: Path, parent: Path) -> bool:
    return path == parent or parent in path.parents


def validate_destination(destination: Path, source_root: Path) -> None:
    assert_plain_path(destination)
    assert_plain_path(source_root)
    if destination == Path(destination.anchor) or destination == absolute_path(Path.home()):
        raise SafetyError(f"Refusing a filesystem root or home directory: {destination}")
    # Source and destination must be independent; never install onto this checkout.
    if is_within(destination, source_root) or is_within(source_root, destination):
        raise SafetyError(f"Source and destination overlap: {source_root} / {destination}")
    if is_within(destination, source_root.parent):
        raise SafetyError(f"Destination must be outside the source checkout: {destination}")
    if os.name == "nt":
        for variable in ("SystemRoot", "ProgramFiles", "ProgramFiles(x86)"):
            value = os.environ.get(variable)
            if value and is_within(destination, absolute_path(value)):
                raise SafetyError(f"Refusing a system directory: {destination}")
    else:
        for name in ("bin", "sbin", "etc", "usr", "lib", "lib64", "boot", "dev", "proc", "sys"):
            if is_within(destination, Path("/") / name):
                raise SafetyError(f"Refusing a system directory: {destination}")
    if exists(destination) and not destination.is_dir():
        raise SafetyError(f"Destination is not a directory: {destination}")
    for reserved in (".codex-skill-backups", ".codex-skill-staging"):
        path = destination / reserved
        assert_plain_path(path)
        if exists(path) and not path.is_dir():
            raise SafetyError(f"Reserved maintenance path is not a directory: {path}")


def make_plan(source_root: Path, destination: Path, names: list[str]) -> list[Plan]:
    validate_destination(destination, source_root)
    if not source_root.is_dir():
        raise SafetyError(f"Skill source directory is missing: {source_root}")
    unknown = set(names) - set(SKILL_NAMES)
    if unknown:
        raise SafetyError(f"Unknown skill name(s): {', '.join(sorted(unknown))}")
    plans = []
    for name in dict.fromkeys(names):
        source, target = source_root / name, destination / name
        source_digest = tree_digest(source)
        entry = source / "SKILL.md"
        if not entry.is_file():
            raise SafetyError(f"Missing skill entry point: {entry}")
        fields = frontmatter(entry.read_text(encoding="utf-8-sig"))
        if fields.get("name") != name or not fields.get("description", "").strip():
            raise SafetyError(f"Invalid name/description in {entry}")
        previous = tree_digest(target) if exists(target) else None
        action = "unchanged" if source_digest == previous else "update" if previous is not None else "install"
        plans.append(Plan(name, source, target, action, source_digest, previous))
    return plans


def _move(source: Path, target: Path) -> None:
    assert_plain_path(source)
    assert_plain_path(target)
    if exists(target):
        raise SafetyError(f"Refusing to overwrite an unexpected path: {target}")
    source.rename(target)


def install_skills(
    source_root: Path,
    destination: Path,
    names: list[str],
    *,
    dry_run: bool = False,
) -> dict:
    source_root, destination = absolute_path(source_root), absolute_path(destination)
    plans = make_plan(source_root, destination, names)
    result = {
        "destination": str(destination),
        "dry_run": dry_run,
        "skills": [{"name": p.name, "action": p.action} for p in plans],
        "backup": None,
    }
    changed = [p for p in plans if p.action != "unchanged"]
    if dry_run or not changed:
        return result

    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ") + "-" + uuid.uuid4().hex[:10]
    staging = destination / ".codex-skill-staging" / run_id
    backup = destination / ".codex-skill-backups" / run_id
    validate_destination(destination, source_root)
    staging.mkdir(parents=True, exist_ok=False)
    moved: list[Plan] = []
    backed_up: list[Plan] = []
    try:
        # Stage everything before touching any installed skill.
        for plan in changed:
            if tree_digest(plan.source) != plan.source_digest:
                raise SafetyError(f"Source changed during installation: {plan.source}")
            shutil.copytree(plan.source, staging / plan.name, symlinks=True)
            if tree_digest(staging / plan.name) != plan.source_digest:
                raise SafetyError(f"Staged content does not match source: {plan.name}")

        if any(p.previous_digest is not None for p in changed):
            backup.mkdir(parents=True, exist_ok=False)
            manifest = {
                "created_at_utc": datetime.now(timezone.utc).isoformat(),
                "destination": str(destination),
                "source": str(source_root),
                "restore": (
                    "Each named subdirectory contains the previous complete skill. "
                    "To roll back, first move the current installed directory to a new safe location; "
                    "then move this backup directory to its original destination. Do not merge versions."
                ),
                "skills": [
                    {"name": p.name, "restore_to": str(p.target)}
                    for p in changed if p.previous_digest is not None
                ],
            }
            (backup / "restore.json").write_text(
                json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
            )

        for plan in changed:
            current = tree_digest(plan.target) if exists(plan.target) else None
            if current != plan.previous_digest:
                raise SafetyError(f"Installed skill changed during installation: {plan.target}")
            if plan.previous_digest is not None:
                _move(plan.target, backup / plan.name)
                backed_up.append(plan)
            _move(staging / plan.name, plan.target)
            moved.append(plan)
    except Exception as error:
        # Restore this batch without deleting files. Keep staged/failed versions for inspection.
        recovery_errors = []
        for plan in reversed(moved):
            try:
                if tree_digest(plan.target) != plan.source_digest:
                    raise SafetyError(f"Installed files were modified; preserve them at {plan.target}")
                _move(plan.target, staging / plan.name)
            except Exception as recovery_error:
                recovery_errors.append(str(recovery_error))
        for plan in reversed(backed_up):
            try:
                _move(backup / plan.name, plan.target)
            except Exception as recovery_error:
                recovery_errors.append(str(recovery_error))
        detail = f"Installation failed: {error}. Staging retained: {staging}."
        if backup.exists():
            detail += f" Recovery records: {backup}."
        if recovery_errors:
            detail += " Manual recovery required: " + "; ".join(recovery_errors)
        else:
            detail += " Changes made to installed skills by this batch were rolled back."
        raise SafetyError(detail) from error

    # Only remove an empty directory created by this invocation; never recursively delete.
    staging.rmdir()
    if backed_up:
        result["backup"] = str(backup)
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dest", type=Path, help="User-level skills directory; default: CODEX_HOME/skills or ~/.codex/skills")
    parser.add_argument("--skill", action="append", nargs="+", metavar="NAME", help="Install only these skills; repeatable (default: all eight)")
    parser.add_argument("--dry-run", action="store_true", help="Show install/update/unchanged actions without creating any files")
    args = parser.parse_args(argv)
    names = [name for group in args.skill for name in group] if args.skill else list(SKILL_NAMES)
    try:
        result = install_skills(REPO_ROOT / "skills", args.dest or default_destination(), names, dry_run=args.dry_run)
    except (OSError, ValueError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print(f"{'DRY RUN: ' if args.dry_run else ''}{result['destination']}")
    for item in result["skills"]:
        print(f"  {item['action']:9} {item['name']}")
    if result["backup"]:
        print(f"Previous versions / rollback instructions: {result['backup']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
