"""Interactive terminal entry point for the Saodi (扫地僧) agent."""

import argparse
import asyncio
import json
import logging
import os
import re
import shlex
import subprocess
import sys
import time

from ..config import load_env
from ..core.client import GausiumAPIClient
from ..v3.api import GausiumV3
from .core import SaodiAgent
from .prompts import build_system_prompt
from .session import AgentSession
from .settings import AgentSettings, build_provider


class TerminalConfirmGate:
    async def ask(self, session_id, confirm_id, name, input, summary) -> bool:
        answer = await asyncio.to_thread(input_fn, f"Approve {summary}? [y/N] ")
        return answer.strip().lower() in {"y", "yes"}


def input_fn(prompt: str) -> str:
    return input(prompt)


async def _repl(args: argparse.Namespace) -> None:
    overrides = {}
    if args.provider:
        overrides["saodi_provider"] = args.provider
    if args.model:
        overrides["saodi_model"] = args.model
    if args.auto_approve:
        overrides["saodi_auto_approve"] = True
    settings = AgentSettings(**overrides)
    provider = build_provider(settings)
    session = AgentSession()
    from ..store import install_call_log

    install_call_log()
    async with GausiumAPIClient() as client:
        agent = SaodiAgent(
            GausiumV3(client), provider, auto_approve=settings.saodi_auto_approve,
            max_turns=settings.saodi_max_turns, confirm_gate=TerminalConfirmGate(),
        )
        if args.robot:
            session.messages.append({"role": "user", "content": f"In this session, operate only robot {args.robot}."})
        while True:
            try:
                user_text = await asyncio.to_thread(input_fn, "\nyou> ")
            except (EOFError, KeyboardInterrupt):
                print()
                break
            if not user_text.strip():
                continue
            if user_text.strip().lower() in {"exit", "quit"}:
                break
            async for event in agent.run(session, user_text):
                if event["type"] == "text_delta":
                    print(event["text"], end="", flush=True)
                elif event["type"] == "tool_call":
                    print(f"\n⚙ {event['name']}({json.dumps(event['input'], ensure_ascii=False)})")
                elif event["type"] == "error":
                    print(f"\nerror: {event['message']}")
            print()


def _when(ts: float | None) -> str:
    return time.strftime("%m-%d %H:%M:%S", time.localtime(ts)) if ts else "-"


def _cut(text, width: int) -> str:
    text = " ".join(str(text or "").split())
    return text if len(text) <= width else text[:width - 1] + "…"


def _print_threads(threads: list[dict]) -> None:
    header = f"{'ID':>4}  {'STATUS':<8} {'CATEGORY':<18} {'COUNT':>5} {'SN':>3}  " \
             f"{'TOOL':<26} {'CODE':<22} {'LAST SEEN':<14}  MSG"
    print(header)
    for t in threads:
        code = t["code"] or t["error_class"]
        print(f"{t['id']:>4}  {t['status']:<8} {t['category']:<18} {t['count']:>5} "
              f"{t['sn_count']:>3}  {_cut(t['tool'], 26):<26} {_cut(code, 22):<22} "
              f"{_when(t['last_seen']):<14}  {_cut(t['sample_msg'], 60)}")
    print(f"({len(threads)} thread(s))")


def _print_thread(t: dict) -> None:
    for key in ("id", "fingerprint", "tool", "error_class", "code", "status", "category",
                "count", "sn_count", "note"):
        print(f"{key:<12} {t[key]}")
    print(f"{'first_seen':<12} {_when(t['first_seen'])}\n{'last_seen':<12} {_when(t['last_seen'])}")
    if t["reopened_at"]:
        print(f"{'reopened_at':<12} {_when(t['reopened_at'])}")
    print(f"{'failure':<12} {t['tool_errors_total']}/{t['tool_calls_total']} calls of this tool")
    print(f"{'trace_ids':<12} {', '.join(t['trace_ids']) or '-'}")
    print(f"{'sample_msg':<12} {t['sample_msg']}\n\nrecent calls:")
    for c in t["calls"]:
        print(f"  {_when(c['ts'])} {c['source']:<7} {c['duration_ms'] or 0:>7.0f}ms "
              f"http={c['http_status']} code={c['code']} trace={c['trace_id']} "
              f"endpoint={c['endpoint']} args={_cut(c['args'], 120)}")


PROMOTED_MARK = "[promoted to memory"
_TRACE_LIKE = re.compile(r"\b[0-9a-f]{16,}\b|\b[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12}\b",
                         re.IGNORECASE)


def lesson_from_thread(thread: dict) -> str:
    """The thread's note (minus the promotion marker), else category + tool + code + sample msg."""
    note = thread["note"].split(PROMOTED_MARK)[0].strip()
    if note:
        return note
    code = thread["code"] or thread["error_class"]
    msg = _TRACE_LIKE.sub("<id>", " ".join(str(thread["sample_msg"] or "").split()))
    return f"{thread['tool']} error {code} ({thread['category']}): {msg}"


def _promote(log, thread_id: int) -> int:
    from ..store.memory import MemoryRejected, add_lesson, local_today

    thread = log.get_thread_sync(thread_id, calls=0)
    if thread is None:
        print(f"thread {thread_id} not found", file=sys.stderr)
        return 1
    if PROMOTED_MARK in thread["note"]:
        print(f"thread {thread_id} is already promoted: {thread['note']}", file=sys.stderr)
        return 1
    try:
        result = add_lesson(lesson_from_thread(thread), "error-code")
    except MemoryRejected as exc:
        print(f"not promoted: {exc}. Write a clean note first "
              f"(PATCH /api/v1/errors/threads/{thread_id}) and retry.", file=sys.stderr)
        return 1
    mark = f"{PROMOTED_MARK} {local_today().isoformat()}]"
    log.update_thread_sync(thread_id, note=f"{thread['note'].strip()} {mark}".strip())
    print(f"{result.status}: {result.entry}\n-> {result.path}")
    return 0


def errors_main(argv: list[str], prog: str = "saodi") -> int:
    """``saodi errors [...]`` / ``show <id>`` / ``promote <id>``: the local error threads."""
    from ..store import CATEGORIES, STATUSES, get_call_log

    parser = argparse.ArgumentParser(prog=f"{prog} errors", description="Tool-call error threads")
    parser.add_argument("action", nargs="?", choices=["list", "show", "promote"], default="list")
    parser.add_argument("thread_id", nargs="?", type=int)
    parser.add_argument("--status", choices=STATUSES)
    parser.add_argument("--category", choices=CATEGORIES)
    parser.add_argument("--limit", type=int, default=100)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    log = get_call_log()
    if args.action in {"show", "promote"} and args.thread_id is None:
        parser.error(f"{args.action} needs a thread id")
    if args.action == "promote":
        return _promote(log, args.thread_id)
    if args.action == "show":
        thread = log.get_thread_sync(args.thread_id)
        if thread is None:
            print(f"thread {args.thread_id} not found", file=sys.stderr)
            return 1
        print(json.dumps(thread, ensure_ascii=False, indent=2)) if args.json else _print_thread(thread)
        return 0
    threads = log.list_threads_sync(status=args.status, category=args.category, limit=args.limit)
    print(json.dumps(threads, ensure_ascii=False, indent=2)) if args.json else _print_threads(threads)
    return 0


def memory_main(argv: list[str], prog: str = "saodi") -> int:
    """``saodi memory`` / ``memory add "<lesson>"`` / ``memory edit``: the local memory file."""
    from ..store.memory import MemoryRejected, add_lesson, ensure_file, memory_path, read_text

    parser = argparse.ArgumentParser(prog=f"{prog} memory",
                                     description="Show, add to or edit Saodi's local memory")
    parser.add_argument("action", nargs="?", choices=["show", "add", "edit"], default="show")
    parser.add_argument("lesson", nargs="?")
    parser.add_argument("--scope", help="optional topic, e.g. error-code, robot, preference")
    args = parser.parse_args(argv)
    if args.action == "add":
        if not args.lesson:
            parser.error('add needs a lesson, e.g. saodi memory add "..."')
        try:
            result = add_lesson(args.lesson, args.scope)
        except MemoryRejected as exc:
            print(f"rejected: {exc}", file=sys.stderr)
            return 1
        print(f"{result.status}: {result.entry}\n-> {result.path}")
        return 0
    if args.action == "edit":
        path = ensure_file()
        editor = os.environ.get("VISUAL") or os.environ.get("EDITOR") or "vi"
        return subprocess.call([*shlex.split(editor), str(path)])
    path = memory_path()
    text = read_text(path)
    print(f"# {path}{'' if text else ' (empty)'}")
    if text:
        print(text, end="" if text.endswith("\n") else "\n")
    return 0


def main(argv: list[str] | None = None, prog: str = "saodi") -> None:
    argv = sys.argv[1:] if argv is None else argv
    load_env()  # ./.env: SAODI_*, SAODI_DATA_DIR, provider keys, GS_* credentials
    if argv[:1] == ["errors"]:
        raise SystemExit(errors_main(argv[1:], prog))
    if argv[:1] == ["memory"]:
        raise SystemExit(memory_main(argv[1:], prog))
    parser = argparse.ArgumentParser(prog=prog, description="Saodi (扫地僧): terminal assistant for Gausium robots. "
                                     "Subcommands: memory, errors (see `saodi memory -h`, `saodi errors -h`).")
    parser.add_argument("--provider", choices=["anthropic", "openai"])
    parser.add_argument("--model")
    parser.add_argument("--auto-approve", action="store_true")
    parser.add_argument("--robot", help="robot SN this session is limited to")
    parser.add_argument(
        "--show-context", action="store_true",
        help="print the final system prompt (Soul/Knowledge/Memory/private) and exit; "
             "no LLM key needed",
    )
    args = parser.parse_args(argv)
    # Context/deprecation notes go to stderr so --show-context stdout stays clean.
    logging.basicConfig(level=logging.WARNING, stream=sys.stderr,
                        format="%(levelname)s %(name)s: %(message)s")
    if args.show_context:
        print(build_system_prompt())
        return
    asyncio.run(_repl(args))


def legacy_main() -> None:
    """Deprecated ``pi-agent`` command; same behaviour as ``saodi`` for one release."""
    print("pi-agent is deprecated; use saodi instead (it goes away next release)", file=sys.stderr)
    main(prog="pi-agent")


if __name__ == "__main__":
    main()
