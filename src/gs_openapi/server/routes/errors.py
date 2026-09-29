"""Error threads: failed tool calls folded by fingerprint (see ARCHITECTURE_V3 §5.2)."""

from typing import Literal

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from gs_openapi.store import get_call_log

router = APIRouter(prefix="/errors/threads")

Status = Literal["open", "expected", "fixed", "wontfix"]
Category = Literal["our_bug", "account_permission", "robot_offline", "upstream",
                   "input_error", "unknown"]


class ThreadPatch(BaseModel):
    status: Status | None = None
    category: Category | None = None
    note: str | None = None


@router.get("")
async def list_threads(
    status: Status | None = None, category: Category | None = None,
    limit: int = Query(100, ge=1, le=1000),
) -> dict:
    return {"items": await get_call_log().list_threads(
        status=status, category=category, limit=limit)}


@router.get("/{thread_id}")
async def get_thread(thread_id: int) -> dict:
    thread = await get_call_log().get_thread(thread_id)
    if thread is None:
        raise HTTPException(status_code=404, detail="Thread not found")
    return thread


@router.patch("/{thread_id}")
async def patch_thread(thread_id: int, body: ThreadPatch) -> dict:
    thread = await get_call_log().update_thread(thread_id, **body.model_dump(exclude_none=True))
    if thread is None:
        raise HTTPException(status_code=404, detail="Thread not found")
    return thread
