"""Single source of truth for V3 tool definitions and model-facing schemas."""

from __future__ import annotations

import inspect
import logging
import time
from collections.abc import Awaitable, Callable, Iterator
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass
from typing import Any, get_type_hints

from pydantic import BaseModel, ValidationError

from ..v3.api import GausiumV3

logger = logging.getLogger(__name__)


class ToolInputError(ValueError):
    """Tool arguments failed validation."""


@dataclass
class ToolSpec:
    name: str
    description: str
    input_model: type[BaseModel]
    handler: Callable[[GausiumV3, BaseModel], Awaitable[Any]]
    dangerous: bool = False
    category: str = "robots"
    local: bool = False  # answers from local files only; needs no upstream client


REGISTRY: dict[str, ToolSpec] = {}


def register(spec: ToolSpec) -> ToolSpec:
    if spec.name in REGISTRY:
        raise ValueError(f"Duplicate tool: {spec.name}")
    REGISTRY[spec.name] = spec
    return spec


def tool(*, name: str, description: str, dangerous: bool = False, category: str = "robots",
         local: bool = False):
    """Register an async handler; its second argument's annotation is its input model."""
    def decorate(handler):
        model = get_type_hints(handler)["args"]
        register(ToolSpec(name, description, model, handler, dangerous, category, local))
        return handler
    return decorate


def get_tool(name: str) -> ToolSpec:
    return REGISTRY[name]


def list_tools(category: str | None = None) -> list[ToolSpec]:
    return [spec for spec in REGISTRY.values() if category is None or spec.category == category]


def _jsonable(value: Any) -> Any:
    if isinstance(value, BaseModel):
        return value.model_dump(mode="json", by_alias=True)
    if isinstance(value, dict):
        return {k: _jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_jsonable(item) for item in value]
    return value


@dataclass
class ToolCall:
    """What call observers receive once per ``invoke`` (success or failure)."""

    tool: str
    args: dict
    source: str
    session_id: str | None
    started_at: float
    duration_ms: float
    error: BaseException | None = None


CallObserver = Callable[[ToolCall], Awaitable[None] | None]
_observers: list[CallObserver] = []
_context: ContextVar[tuple[str, str | None]] = ContextVar("tool_call_context", default=("unknown", None))


def add_call_observer(fn: CallObserver) -> None:
    if fn not in _observers:
        _observers.append(fn)


def remove_call_observer(fn: CallObserver) -> None:
    if fn in _observers:
        _observers.remove(fn)


@contextmanager
def call_context(source: str, session_id: str | None = None) -> Iterator[None]:
    """Tag tool calls made inside this block with their entry point (agent/rest/mcp)."""
    token = _context.set((source, session_id))
    try:
        yield
    finally:
        _context.reset(token)


async def _notify(call: ToolCall) -> None:
    for observer in _observers:
        try:
            result = observer(call)
            if inspect.isawaitable(result):
                await result
        except Exception:
            logger.warning("tool call observer failed for %s", call.tool, exc_info=True)


async def invoke(name: str, args: dict, v3: GausiumV3) -> Any:
    """Validate and run one tool; the single choke point every entry point goes through."""
    source, session_id = _context.get()
    started_at, start = time.time(), time.perf_counter()
    error: BaseException | None = None
    try:
        spec = get_tool(name)
        try:
            validated = spec.input_model.model_validate(args)
        except ValidationError as exc:
            raise ToolInputError(f"Invalid input for {name}: {exc}") from exc
        return _jsonable(await spec.handler(v3, validated))
    except BaseException as exc:
        error = exc
        raise
    finally:
        # Cancellation/interpreter exit is not a tool outcome; awaiting here would re-raise anyway.
        if _observers and (error is None or isinstance(error, Exception)):
            await _notify(ToolCall(name, args if isinstance(args, dict) else {"_": args},
                                   source, session_id, started_at,
                                   (time.perf_counter() - start) * 1000, error))


def _strip_titles(schema: Any) -> Any:
    if isinstance(schema, dict):
        return {key: _strip_titles(value) for key, value in schema.items() if key != "title"}
    if isinstance(schema, list):
        return [_strip_titles(item) for item in schema]
    return schema


def _schema(spec: ToolSpec) -> dict:
    schema = _strip_titles(spec.input_model.model_json_schema())
    schema["additionalProperties"] = False
    return schema


def to_anthropic_tools() -> list[dict]:
    return [{"name": spec.name, "description": spec.description, "input_schema": _schema(spec)}
            for spec in REGISTRY.values()]


def to_openai_tools() -> list[dict]:
    return [{"type": "function", "function": {"name": spec.name,
            "description": spec.description, "parameters": _schema(spec)}}
            for spec in REGISTRY.values()]


# Populate the registry when importing it directly as well as through the package.
from . import knowledge_tools, v3_tools, workflow_tools  # noqa: F401
