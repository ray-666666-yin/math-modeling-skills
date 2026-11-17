#!/usr/bin/env python3
"""Check the eight distributable skills using only Python's standard library."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from urllib.parse import unquote, urlsplit

from skill_common import REPO_ROOT, SKILL_NAMES, SafetyError, absolute_path, frontmatter, tree_digest


HOME_PATH = re.compile(r"(?i)(?:[a-z]:[\\/]+Users[\\/]+[^\s\"'<>`/\\]+|/(?:Users|home)/[^\s\"'<>`/\\]+)")
PLACEHOLDER_USERS = {"user", "username", "yourname", "your-name", "you", "example", "用户名", "用户"}
SECRET_PATTERNS = (
    ("private key", re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----")),
    ("API key", re.compile(r"\bsk-(?:proj-|ant-)?[A-Za-z0-9_-]{24,}\b")),
    ("GitHub token", re.compile(r"\b(?:gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{40,})\b")),
    ("AWS access key", re.compile(r"\b(?:AKIA|ASIA)[A-Z0-9]{16}\b")),
    ("bearer JWT", re.compile(r"(?i)Bearer\s+eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}")),
)
TEXT_SUFFIXES = {".md", ".py", ".m", ".tex", ".typ", ".json", ".yaml", ".yml", ".txt", ".csv", ".toml", ".xml", ".svg", ".drawio", ".ps1", ".sh", ".bib"}


def markdown_links(text: str):
    """Yield local/remote Markdown destinations outside fenced code blocks."""
    fence = None
    for number, line in enumerate(text.splitlines(), 1):
        marker = re.match(r"^\s*(`{3,}|~{3,})", line)
        if marker:
            token = marker.group(1)
            if fence is None:
                fence = (token[0], len(token))
            elif token[0] == fence[0] and len(token) >= fence[1]:
                fence = None
            continue
        if fence is not None:
            continue
        destinations = re.findall(r"!?\[[^\]]*\]\((<[^>]+>|[^\n)]+)\)", line)
        definition = re.match(r"^\s{0,3}\[[^\]]+\]:\s*(<[^>]+>|\S+)", line)
        if definition:
            destinations.append(definition.group(1))
        for destination in destinations:
            destination = destination.strip()
            if destination.startswith("<") and ">" in destination:
                destination = destination[1:destination.index(">")]
            else:
                # A quoted title is optional; a bare local path may contain spaces.
                destination = re.split(r"\s+[\"']", destination, maxsplit=1)[0].strip()
            yield number, destination


def check_repository(root: Path) -> list[str]:
    root = absolute_path(root)
    skill_root = root / "skills"
    errors: list[str] = []
    try:
        tree_digest(skill_root)
    except (OSError, SafetyError) as error:
        return [str(error)]
    actual = {path.name for path in skill_root.iterdir() if path.is_dir()}
    for name in sorted(set(SKILL_NAMES) - actual):
        errors.append(f"skills/{name}: required skill is missing")
    for name in sorted(actual - set(SKILL_NAMES)):
        errors.append(f"skills/{name}: not in the reviewed eight-skill release manifest")

    for name in SKILL_NAMES:
        folder = skill_root / name
        if not folder.is_dir():
            continue
        entry = folder / "SKILL.md"
        try:
            fields = frontmatter(entry.read_text(encoding="utf-8-sig"))
            if fields.get("name") != name:
                errors.append(f"skills/{name}/SKILL.md: name must match its directory")
            if not fields.get("description", "").strip():
                errors.append(f"skills/{name}/SKILL.md: description is empty")
        except (OSError, UnicodeError, ValueError) as error:
            errors.append(f"skills/{name}/SKILL.md: {error}")

        for path in sorted(folder.rglob("*")):
            if not path.is_file() or path.suffix.lower() not in TEXT_SUFFIXES:
                continue
            label = path.relative_to(root).as_posix()
            try:
                text = path.read_text(encoding="utf-8-sig")
            except (OSError, UnicodeError) as error:
                errors.append(f"{label}: cannot read as UTF-8: {error}")
                continue
            for line_number, line in enumerate(text.splitlines(), 1):
                for match in HOME_PATH.finditer(line):
                    username = re.split(r"[\\/]", match.group())[-1].casefold()
                    if username not in PLACEHOLDER_USERS and not username.startswith(("$", "%", "{")):
                        # Do not print potentially private path text in CI output.
                        errors.append(f"{label}:{line_number}: workstation-specific home path")
                for kind, pattern in SECRET_PATTERNS:
                    if pattern.search(line):
                        errors.append(f"{label}:{line_number}: possible {kind}; inspect locally (value redacted)")
            if path.suffix.lower() != ".md":
                continue
            for line_number, destination in markdown_links(text):
                if not destination or destination.startswith(("#", "//")):
                    continue
                parsed = urlsplit(destination.replace("\\", "/"))
                if parsed.scheme:
                    if parsed.scheme.lower() == "file" or re.match(r"^[A-Za-z]:[\\/]", destination):
                        errors.append(f"{label}:{line_number}: absolute filesystem link is not portable")
                    continue
                decoded = unquote(parsed.path)
                target = absolute_path(path.parent / decoded)
                if target != folder and folder not in target.parents:
                    errors.append(f"{label}:{line_number}: local link leaves this standalone skill: {destination}")
                elif not target.exists():
                    errors.append(f"{label}:{line_number}: missing local reference: {destination}")
    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=REPO_ROOT, help="Repository root (primarily for isolated checks)")
    args = parser.parse_args(argv)
    errors = check_repository(args.root)
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        print(f"FAILED: {len(errors)} issue(s)", file=sys.stderr)
        return 1
    print(f"OK: {len(SKILL_NAMES)} skills; frontmatter, local Markdown links, personal home paths and common secret patterns checked.")
    print("This static check does not prove skill behavior or exhaustively detect secrets.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
