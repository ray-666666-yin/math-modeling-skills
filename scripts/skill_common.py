"""Small standard-library helpers shared by the maintainer tools."""

from __future__ import annotations

import hashlib
import os
import re
import stat
from pathlib import Path


SKILL_NAMES = (
    "mcm-model-selection",
    "mcm-model-innovation",
    "mcm-model-summary",
    "mcm-word-to-latex",
    "matlab-paper-plotting",
    "mcm-paper-flowcharts",
    "mcm-model-handoff",
    "mcm-result-lineage",
)
REPO_ROOT = Path(__file__).resolve().parents[1]


class SafetyError(ValueError):
    """An operation cannot be performed safely with the supplied paths."""


def absolute_path(path: Path | str) -> Path:
    # Do not resolve links before inspecting them: that would hide the link.
    return Path(os.path.abspath(os.path.expanduser(os.fspath(path))))


def exists(path: Path) -> bool:
    return os.path.lexists(path)


def is_link(path: Path) -> bool:
    info = path.lstat()
    return stat.S_ISLNK(info.st_mode) or bool(
        getattr(info, "st_file_attributes", 0)
        & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)
    )


def assert_plain_path(path: Path) -> None:
    """Reject symlinks/junctions, including existing parent components."""
    for component in (path, *path.parents):
        if exists(component) and is_link(component):
            raise SafetyError(f"Symlink or reparse point is not allowed: {component}")


def tree_digest(root: Path) -> dict[str, str]:
    """Fingerprint regular files and directories, refusing special entries."""
    assert_plain_path(root)
    if not root.is_dir():
        raise SafetyError(f"Expected a directory: {root}")
    result: dict[str, str] = {}
    for parent, directories, files in os.walk(root, followlinks=False):
        for name in sorted(directories + files):
            path = Path(parent) / name
            if is_link(path):
                raise SafetyError(f"Symlink or reparse point is not allowed: {path}")
            mode = path.lstat().st_mode
            key = path.relative_to(root).as_posix()
            if stat.S_ISDIR(mode):
                result[key + "/"] = "directory"
            elif stat.S_ISREG(mode):
                digest = hashlib.sha256()
                with path.open("rb") as stream:
                    for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                        digest.update(chunk)
                result[key] = digest.hexdigest()
            else:
                raise SafetyError(f"Non-regular filesystem entry is not allowed: {path}")
    return result


def frontmatter(text: str) -> dict[str, str]:
    """Read the top-level scalar fields we validate; not a general YAML parser."""
    lines = text.lstrip("\ufeff").splitlines()
    if not lines or lines[0].strip() != "---":
        raise ValueError("SKILL.md must start with YAML frontmatter")
    try:
        end = next(i for i in range(1, len(lines)) if lines[i].strip() == "---")
    except StopIteration as error:
        raise ValueError("YAML frontmatter is not closed") from error
    fields: dict[str, str] = {}
    for index in range(1, end):
        match = re.match(r"^([A-Za-z][\w-]*):\s*(.*)$", lines[index])
        if not match:
            continue
        key, value = match.groups()
        if key in fields:
            raise ValueError(f"Duplicate top-level frontmatter key: {key}")
        if value in {"|", "|-", "|+", ">", ">-", ">+"}:
            continuation = []
            for line in lines[index + 1 : end]:
                if line and not line[0].isspace():
                    break
                continuation.append(line.strip())
            value = " ".join(continuation).strip()
        elif len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
            value = value[1:-1]
        fields[key] = value
    return fields
