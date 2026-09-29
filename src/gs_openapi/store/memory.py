"""Local, private memory file: ``$SAODI_DATA_DIR/memory.md``, one lesson per line.

Entries look like ``- [YYYY-MM-DD] lesson``; the newest entry is appended at the end.
The file is loaded into Saodi's system prompt after the open-source experience.md and is
never written without an explicit request (the ``remember`` tool is dangerous, so the agent
asks for confirmation; ``saodi memory add`` is the user acting directly).
"""

from __future__ import annotations

import os
import re
import threading
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path

from .db import default_data_dir

MEMORY_FILE = "memory.md"
LESSON_MAX = 500
HEADER = (
    "# Saodi local memory\n\n"
    "Private lessons learned on this machine, one per line: `- [YYYY-MM-DD] lesson`.\n"
    "Never commit this file. Do not put credentials here.\n"
)
ENTRY = re.compile(r"^- \[(\d{4}-\d{2}-\d{2})\] (.+)$")
# Credential-looking content is refused: key=value secrets, bearer tokens, prefixed keys,
# JWTs and long high-entropy strings (which also covers trace IDs and access tokens).
_SECRET_PATTERNS = (
    re.compile(r"(?i)\b[\w-]*(?:token|secret|passw(?:or)?d|api[_-]?key|access[_-]?key|"
               r"authorization)[\w-]*\s*[:=]\s*\S+"),
    re.compile(r"(?i)\bbearer\s+[\w.~+/=-]{8,}"),
    re.compile(r"\b(?:sk|ak|pk|rk)-[A-Za-z0-9_-]{8,}"),
    re.compile(r"\beyJ[\w-]{10,}\.[\w-]{10,}"),
    re.compile(r"(?=[A-Za-z0-9+/_=-]*\d)(?=[A-Za-z0-9+/_=-]*[A-Za-z])[A-Za-z0-9+/_=-]{32,}"),
)
_lock = threading.Lock()


class MemoryRejected(ValueError):
    """The lesson is empty, too long or looks like it contains a credential."""


@dataclass
class AddResult:
    status: str        # "added" | "duplicate"
    entry: str
    path: Path


def local_today() -> date:
    return datetime.now().astimezone().date()


def memory_path() -> Path:
    return default_data_dir() / MEMORY_FILE


def _one_line(text: str) -> str:
    return " ".join(str(text).split())


def normalize(lesson: str) -> str:
    """Comparison key for de-duplication: case, whitespace and trailing punctuation ignored."""
    return _one_line(lesson).casefold().rstrip(" .。!！;；")


def contains_secret(text: str) -> bool:
    return any(pattern.search(text) for pattern in _SECRET_PATTERNS)


def compose(lesson: str, scope: str | None = None) -> str:
    """Validate and flatten a lesson (``scope: lesson`` when a scope is given)."""
    body = _one_line(lesson)
    scope = _one_line(scope or "")
    if scope:
        body = f"{scope}: {body}"
    if not _one_line(lesson):
        raise MemoryRejected("lesson is empty")
    if len(body) > LESSON_MAX:
        raise MemoryRejected(f"lesson is longer than {LESSON_MAX} characters; make it shorter")
    if contains_secret(body):
        raise MemoryRejected("lesson looks like it contains a credential or token; refusing to store it")
    return body


def read_text(path: Path | None = None) -> str:
    try:
        return (path or memory_path()).read_text(encoding="utf-8")
    except FileNotFoundError:
        return ""


def entries(text: str) -> list[tuple[str, str]]:
    """``(date, lesson)`` for every well-formed entry line, oldest first."""
    return [(m.group(1), m.group(2)) for line in text.splitlines() if (m := ENTRY.match(line))]


def ensure_file(path: Path | None = None) -> Path:
    path = path or memory_path()
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    if not path.exists():
        fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(HEADER)
    return path


def add_lesson(lesson: str, scope: str | None = None, *, today: date | None = None,
               path: Path | None = None) -> AddResult:
    body = compose(lesson, scope)
    with _lock:
        path = ensure_file(path)
        text = read_text(path)
        key = normalize(body)
        for day, existing in entries(text):
            if normalize(existing) == key:
                return AddResult("duplicate", f"- [{day}] {existing}", path)
        entry = f"- [{(today or local_today()).isoformat()}] {body}"
        with path.open("a", encoding="utf-8") as handle:
            handle.write(("" if text.endswith("\n") or not text else "\n") + entry + "\n")
    return AddResult("added", entry, path)


def trim_oldest(text: str, max_chars: int) -> tuple[str, int]:
    """Drop the oldest entry lines until ``text`` fits; returns ``(text, dropped_count)``.

    Non-entry lines (the header, notes typed in by hand) are kept.
    """
    lines = text.splitlines()
    dropped = 0
    while len("\n".join(lines)) > max_chars:
        index = next((i for i, line in enumerate(lines) if ENTRY.match(line)), None)
        if index is None:
            break
        del lines[index]
        dropped += 1
    return "\n".join(lines), dropped
