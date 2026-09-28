"""Single source of truth for V3 tool definitions and model-facing schemas."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Any, get_type_hints

from pydantic import BaseModel, ValidationError

from ..v3.api import GausiumV3


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


REGISTRY: dict[str, ToolSpec] = {}


def register(spec: ToolSpec) -> ToolSpec:
    if spec.name in REGISTRY:
        raise ValueError(f"Duplicate tool: {spec.name}")
    REGISTRY[spec.name] = spec
    return spec


def tool(*, name: str, description: str, dangerous: bool = False, category: str = "robots"):
    """Register an async handler; its second argument's annotation is its input model."""
    def decorate(handler):
        model = get_type_hints(handler)["args"]
        register(ToolSpec(name, description, model, handler, dangerous, category))
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


async def invoke(name: str, args: dict, v3: GausiumV3) -> Any:
    spec = get_tool(name)
    try:
        validated = spec.input_model.model_validate(args)
    except ValidationError as exc:
        raise ToolInputError(f"Invalid input for {name}: {exc}") from exc
    return _jsonable(await spec.handler(v3, validated))


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
from . import v3_tools, workflow_tools  # noqa: F401
