"""Saodi system prompt: Soul -> Knowledge -> Memory -> optional private context.

Knowledge and the open-source Memory are read from the gs-robot Agent Skill (single
source). A wheel ships it as ``gs_openapi/_skills/gs-robot`` (hatch force-include); a
source checkout reads ``skills/gs-robot`` at the repository root. The local, private
memory ``$SAODI_DATA_DIR/memory.md`` follows the open-source experience. The error-code
table is not resident: the agent looks codes up with the ``lookup_error_code`` tool.
Logs record file names and byte counts only, never content.
"""

import logging
import re
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger(__name__)

_AGENT_DIR = Path(__file__).resolve().parent
SOUL_FILE = _AGENT_DIR / "soul.md"
SKILL_DIRS = (
    _AGENT_DIR.parent / "_skills" / "gs-robot",       # installed wheel
    _AGENT_DIR.parents[2] / "skills" / "gs-robot",    # source checkout / editable
)
KNOWLEDGE_FILES = ("references/domain.md", "SKILL.md", "references/work-states.md")
MEMORY_FILES = ("references/experience.md",)
LOCAL_MEMORY_LABEL = "local memory.md"
DEFAULT_MAX_CHARS = 60_000
_FRONTMATTER = re.compile(r"\A---\n.*?\n---\n", re.DOTALL)


@dataclass
class _Part:
    layer: str
    label: str
    text: str


def find_skill_dir() -> Path | None:
    return next((path for path in SKILL_DIRS if (path / "SKILL.md").is_file()), None)


def _read(layer: str, label: str, path: Path) -> _Part | None:
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        logger.warning("saodi context: %s 文件不可读，已跳过：%s", layer, label)
        return None
    return _Part(layer, label, _FRONTMATTER.sub("", text).strip())


def _local_memory() -> _Part | None:
    from ..store.memory import memory_path

    path = memory_path()
    if not path.is_file():
        return None
    return _read("memory", LOCAL_MEMORY_LABEL, path)


def _fit_local_memory(parts: list[_Part], max_chars: int, sep: str) -> None:
    """Local memory is the elastic layer: when the prompt is over the cap, drop its oldest
    entries first (everything else keeps the plain truncate-and-drop rule)."""
    from ..store.memory import trim_oldest

    local = next((p for p in parts if p.label == LOCAL_MEMORY_LABEL), None)
    total = len(sep.join(_render(p) for p in parts))
    if local is None or total <= max_chars:
        return
    budget = len(local.text) - (total - max_chars)
    local.text, dropped = trim_oldest(local.text, max(budget, 0))
    if dropped:
        logger.warning(
            "saodi context: over the %d-char cap, dropped the %d oldest local memory entries",
            max_chars, dropped)


def collect_parts(context_dir: str | Path | None = None) -> list[_Part]:
    parts = [_read("soul", "soul.md", SOUL_FILE)]
    skill_dir = find_skill_dir()
    if skill_dir is None:
        logger.warning("saodi context: 找不到 gs-robot skill 目录，Knowledge/Memory 未加载")
    else:
        for layer, names in (("knowledge", KNOWLEDGE_FILES), ("memory", MEMORY_FILES)):
            parts += [_read(layer, name, skill_dir / name) for name in names]
    parts.append(_local_memory())
    if context_dir:
        root = Path(context_dir).expanduser()
        if not root.is_dir():
            logger.warning("saodi context: SAODI_CONTEXT_DIR 不是目录，已忽略")
        else:
            parts += [_read("private", path.name, path) for path in sorted(root.glob("*.md"))]
    return [part for part in parts if part is not None]


def _render(part: _Part) -> str:
    return f"<!-- {part.layer}: {part.label} -->\n{part.text}"


def build_system_prompt(
    *, context_dir: str | Path | None = None, max_chars: int | None = None,
) -> str:
    """Assemble the system prompt once per session; defaults come from AgentSettings."""
    if context_dir is None or max_chars is None:
        from .settings import AgentSettings

        settings = AgentSettings()
        context_dir = settings.saodi_context_dir if context_dir is None else context_dir
        max_chars = settings.saodi_context_max_chars if max_chars is None else max_chars
    sep = "\n\n"
    chunks: list[str] = []
    loaded: list[str] = []
    parts = collect_parts(context_dir)
    _fit_local_memory(parts, max_chars, sep)
    for index, part in enumerate(parts):
        chunk = _render(part)
        room = max_chars - len(sep.join(chunks)) - (len(sep) if chunks else 0)
        if len(chunk) > room:
            dropped = [f"{p.layer}:{p.label}" for p in parts[index + 1:]]
            if room > 0:
                chunks.append(chunk[:room])
            logger.warning(
                "saodi context: 超过上限 %d 字符，截断 %s:%s（保留 %d/%d 字符），丢弃 %s",
                max_chars, part.layer, part.label, max(room, 0), len(chunk), dropped or "无",
            )
            loaded.append(f"{part.layer}:{part.label}({max(room, 0)}/{len(chunk)} chars, truncated)")
            break
        chunks.append(chunk)
        loaded.append(f"{part.layer}:{part.label}({len(part.text.encode())} bytes)")
    prompt = sep.join(chunks)
    logger.info("saodi context: 加载 %s，合计 %d 字符", ", ".join(loaded), len(prompt))
    return prompt
