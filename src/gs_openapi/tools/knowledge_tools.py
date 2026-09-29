"""Local knowledge tools: error-code lookup (read-only) and the ``remember`` memory writer."""

from __future__ import annotations

import re
from pathlib import Path

from pydantic import Field, field_validator

from .registry import ToolInputError, tool
from .v3_tools import Input

ERROR_CODE_SOURCES = ("references/error-codes.md", "references/experience.md")
OFFICIAL_ERROR_CODES = ("https://developer.gs-robot.com/v3docs/en_US/OpenAPI%20V3/"
                        "Task%20Startup%20Failure%20Error%20Codes")
MAX_MATCHES = 10


def _is_table_row(line: str) -> bool:
    return line.lstrip().startswith("|")


def _is_separator(line: str) -> bool:
    return bool(re.fullmatch(r"\s*\|[\s|:-]+\|\s*", line))


def search_error_code(code: str, skill_dir: Path | None) -> list[dict]:
    """Every line mentioning ``code`` (as a whole number), with its section heading and,
    for table rows, the table header so the columns stay readable."""
    if skill_dir is None:
        return []
    pattern = re.compile(rf"(?<!\d){re.escape(code)}(?!\d)")
    matches: list[dict] = []
    for name in ERROR_CODE_SOURCES:
        try:
            lines = (skill_dir / name).read_text(encoding="utf-8").splitlines()
        except OSError:
            continue
        section, header = "", ""
        for index, line in enumerate(lines):
            if line.startswith("#"):
                section, header = line.lstrip("#").strip(), ""
                continue
            if _is_table_row(line) and index + 1 < len(lines) and _is_separator(lines[index + 1]):
                header = f"{line}\n{lines[index + 1]}"
                continue
            if not _is_table_row(line):
                header = "" if not line.strip() else header
            if pattern.search(line):
                text = f"{header}\n{line}" if _is_table_row(line) and header else line.strip()
                matches.append({"source": Path(name).name, "section": section, "text": text})
    return matches[:MAX_MATCHES]


class ErrorCode(Input):
    code: str = Field(description="Numeric code, e.g. 230003, 2010100007, 401")

    @field_validator("code", mode="before")
    @classmethod
    def _digits(cls, value):
        text = str(value).strip()
        if not re.fullmatch(r"\d{3,10}", text):
            raise ValueError("code must be 3-10 digits")
        return text


@tool(name="lookup_error_code", category="reference", local=True,
      description="查询错误码含义与处置（本地码表与调用经验）/ "
                  "Look up an error code's meaning and handling in the local reference tables")
async def lookup_error_code(v3, args: ErrorCode):
    from ..agent.prompts import find_skill_dir

    matches = search_error_code(args.code, find_skill_dir())
    result = {"code": args.code, "found": bool(matches), "matches": matches}
    if not matches:
        result["hint"] = ("Not in the local tables. Do not guess its meaning: report the code "
                          f"and the upstream msg as returned, and point to {OFFICIAL_ERROR_CODES}")
    return result


class Remember(Input):
    lesson: str = Field(description="One reusable, verified lesson, one sentence")
    scope: str | None = Field(None, description="Optional topic, e.g. error-code, robot, preference")


@tool(name="remember", category="memory", dangerous=True, local=True,
      description="把一条经证实的可复用经验写入本地记忆（需用户确认）/ "
                  "Save one verified, reusable lesson to local memory (needs user approval)")
async def remember(v3, args: Remember):
    from ..store.memory import MemoryRejected, add_lesson

    try:
        result = add_lesson(args.lesson, args.scope)
    except MemoryRejected as exc:
        raise ToolInputError(str(exc)) from exc
    return {"status": result.status, "entry": result.entry, "path": str(result.path)}
