"""Local memory layer, the remember / lookup_error_code tools and the memory / promote CLI."""

import logging
import re

import pytest

from gs_openapi.agent import prompts
from gs_openapi.agent.cli import main
from gs_openapi.agent.core import SaodiAgent
from gs_openapi.agent.providers.base import MessageEnd, TextDelta, ToolUse
from gs_openapi.agent.session import AgentSession
from gs_openapi.core.errors import GausiumAPIError
from gs_openapi.store import get_call_log
from gs_openapi.store.memory import add_lesson, entries, local_today, memory_path, read_text
from gs_openapi.tools.registry import REGISTRY, ToolCall, ToolInputError, invoke

LOCAL = "<!-- memory: local memory.md -->"


@pytest.fixture(autouse=True)
def no_private_dir(monkeypatch):
    monkeypatch.delenv("SAODI_CONTEXT_DIR", raising=False)
    monkeypatch.delenv("SAODI_CONTEXT_MAX_CHARS", raising=False)


def markers(prompt: str) -> list[str]:
    return [line for line in prompt.splitlines() if line.startswith("<!-- ")]


# --- loading ----------------------------------------------------------------------------

def test_local_memory_loads_after_experience_before_private_dir(tmp_path):
    add_lesson("Robot A beeps twice before docking; that is normal.")
    private = tmp_path / "ctx"
    private.mkdir()
    (private / "a.md").write_text("private note", encoding="utf-8")
    prompt = prompts.build_system_prompt(context_dir=private, max_chars=10**9)
    assert markers(prompt)[-3:] == [
        "<!-- memory: references/experience.md -->", LOCAL, "<!-- private: a.md -->"]
    assert "beeps twice before docking" in prompt


def test_missing_memory_file_is_silently_skipped(caplog):
    with caplog.at_level(logging.WARNING, logger="gs_openapi.agent.prompts"):
        prompt = prompts.build_system_prompt(max_chars=10**9)
    assert LOCAL not in prompt and not caplog.records


def test_over_cap_drops_oldest_memory_entries_first(tmp_path, caplog):
    for n in range(1, 4):
        add_lesson(f"lesson number {n} " + "x" * 40)
    private = tmp_path / "ctx"
    private.mkdir()
    (private / "z.md").write_text("PRIVATE TAIL", encoding="utf-8")
    full = prompts.build_system_prompt(context_dir=private, max_chars=10**9)
    limit = len(full) - 30  # room for everything except roughly one entry
    with caplog.at_level(logging.WARNING, logger="gs_openapi.agent.prompts"):
        prompt = prompts.build_system_prompt(context_dir=private, max_chars=limit)
    assert len(prompt) <= limit
    assert "lesson number 1" not in prompt
    assert "lesson number 2" in prompt and "lesson number 3" in prompt
    assert prompt.endswith("PRIVATE TAIL")  # later layers are not cut
    assert "dropped the 1 oldest local memory entries" in caplog.text


# --- remember ---------------------------------------------------------------------------

def test_remember_is_dangerous_local_and_bilingual():
    spec = REGISTRY["remember"]
    assert spec.dangerous and spec.local and spec.category == "memory"
    assert "/" in spec.description
    lookup = REGISTRY["lookup_error_code"]
    assert not lookup.dangerous and lookup.local and lookup.category == "reference"


async def test_remember_writes_one_line_and_dedups():
    first = await invoke("remember", {"lesson": "  110003 on reports means the app is\nnot bound. "},
                         None)
    again = await invoke("remember", {"lesson": "110003 ON REPORTS means the app is not bound."},
                         None)
    scoped = await invoke("remember", {"lesson": "prefers tables", "scope": "preference"}, None)
    assert (first["status"], again["status"], scoped["status"]) == ("added", "duplicate", "added")
    text = read_text()
    assert re.search(r"^- \[\d{4}-\d{2}-\d{2}\] 110003 on reports means the app is not bound\.$",
                     text, re.MULTILINE)
    assert [lesson for _, lesson in entries(text)] == [
        "110003 on reports means the app is not bound.", "preference: prefers tables"]
    assert memory_path().stat().st_mode & 0o777 == 0o600


@pytest.mark.parametrize("lesson", [
    "use Authorization: Bearer zyxwvutsrqponm",
    "client_secret=s3cr3t-value",
    "the api_key: live-123",
    "key is sk-zyxwvutsrqponmlkjih",
    "trace 0123456789abcdef0123456789abcdef",
    "jwt eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.abc",
    "   ",
])
async def test_remember_rejects_secret_like_or_empty_lessons(lesson):
    with pytest.raises(ToolInputError):
        await invoke("remember", {"lesson": lesson}, None)
    assert entries(read_text()) == []


def test_plain_mentions_of_tokens_are_allowed():
    assert add_lesson("The access token expires after 24h; token_manager refreshes it.").status \
        == "added"


class ScriptedProvider:
    """First turn asks for remember, second turn just answers."""

    def __init__(self):
        self.turn = 0

    async def stream(self, *, system, messages, tools):
        self.turn += 1
        if self.turn == 1:
            block = {"type": "tool_use", "id": "r1", "name": "remember",
                     "input": {"lesson": "230003 means the robot is offline"}}
            yield ToolUse("r1", "remember", block["input"])
            yield MessageEnd("tool_use", {}, [block])
        else:
            yield TextDelta("ok")
            yield MessageEnd("end_turn", {}, [{"type": "text", "text": "ok"}])


class Gate:
    def __init__(self, approve):
        self.approve, self.asked = approve, []

    async def ask(self, session_id, confirm_id, name, input, summary):
        self.asked.append(name)
        return self.approve


@pytest.mark.parametrize("approve", [False, True])
async def test_remember_goes_through_the_confirmation_gate(approve):
    gate = Gate(approve)
    agent = SaodiAgent(None, ScriptedProvider(), confirm_gate=gate)
    session = AgentSession(system_prompt="SYS")
    events = [e async for e in agent.run(session, "remember that")]
    assert gate.asked == ["remember"]
    assert any(e["type"] == "confirm_required" for e in events)
    result = next(e for e in events if e["type"] == "tool_result")
    assert result["is_error"] is (not approve)
    stored = [lesson for _, lesson in entries(read_text())]
    assert stored == (["230003 means the robot is offline"] if approve else [])


# --- lookup_error_code ------------------------------------------------------------------

async def test_lookup_finds_official_table_row_with_header():
    result = await invoke("lookup_error_code", {"code": 2010100007}, None)
    assert result["found"] and result["code"] == "2010100007"
    row = next(m for m in result["matches"] if m["source"] == "error-codes.md")
    assert "Task area unreachable" in row["text"] and row["text"].startswith("|")
    assert row["text"].count("\n") >= 2  # header + separator + row


async def test_lookup_finds_experience_entries_and_whole_numbers_only():
    result = await invoke("lookup_error_code", {"code": "230003"}, None)
    assert any(m["source"] == "experience.md" and "routing failed" in m["text"]
               for m in result["matches"])
    miss = await invoke("lookup_error_code", {"code": "30003"}, None)  # not a substring match
    assert miss["found"] is False and "Do not guess" in miss["hint"]


async def test_lookup_validates_code():
    with pytest.raises(ToolInputError):
        await invoke("lookup_error_code", {"code": "abc"}, None)


# --- CLI --------------------------------------------------------------------------------

def run_cli(argv):
    with pytest.raises(SystemExit) as done:
        main(argv)
    return done.value.code


def test_cli_memory_show_add_and_reject(capsys):
    assert run_cli(["memory"]) == 0
    assert "(empty)" in capsys.readouterr().out
    assert run_cli(["memory", "add", "Prefer online robots for probes", "--scope", "robot"]) == 0
    assert "added: - [" in capsys.readouterr().out
    assert run_cli(["memory", "add", "prefer online robots for probes.", "--scope", "robot"]) == 0
    assert "duplicate" in capsys.readouterr().out
    assert run_cli(["memory", "add", "password=hunter2"]) == 1
    assert "rejected" in capsys.readouterr().err
    assert run_cli(["memory"]) == 0
    out = capsys.readouterr().out
    assert str(memory_path()) in out and "robot: Prefer online robots for probes" in out
    assert "hunter2" not in read_text()


def test_cli_memory_edit_uses_editor(monkeypatch, tmp_path):
    seen = tmp_path / "seen"
    monkeypatch.setenv("VISUAL", f"sh -c 'cp \"$0\" {seen}'")
    assert run_cli(["memory", "edit"]) == 0
    assert seen.read_text(encoding="utf-8").startswith("# Saodi local memory")


async def test_cli_errors_promote_note_then_fallback(capsys):
    log = get_call_log()
    exc = GausiumAPIError("Robot X routing failed.", code=230003, trace_id="t-1",
                          http_status=200, endpoint="v3_robots_status_get")
    await log.observe(ToolCall("get_robot_status", {"robot_sn_list": ["SN"]}, "rest", None,
                               1000.0, 5.0, exc))
    exc2 = GausiumAPIError("Something 0123456789abcdef0123 broke", code=999999, trace_id="t-2",
                           http_status=200, endpoint="v3_x")
    await log.observe(ToolCall("list_robot_maps", {"robot_sn": "SN"}, "rest", None,
                               1001.0, 5.0, exc2))
    by_tool = {t["tool"]: t["id"] for t in await log.list_threads()}
    noted = by_tool["get_robot_status"]
    log.update_thread_sync(noted, note="230003 on batch status: filter by list_robots online first")

    assert run_cli(["errors", "promote", str(noted)]) == 0
    assert "added" in capsys.readouterr().out
    thread = log.get_thread_sync(noted, calls=0)
    today = local_today().isoformat()
    assert thread["note"].endswith(f"[promoted to memory {today}]")
    assert run_cli(["errors", "promote", str(noted)]) == 1  # already promoted
    assert "already promoted" in capsys.readouterr().err

    assert run_cli(["errors", "promote", str(by_tool["list_robot_maps"])]) == 0
    lessons = [lesson for _, lesson in entries(read_text())]
    assert lessons[0] == "error-code: 230003 on batch status: filter by list_robots online first"
    assert lessons[1] == ("error-code: list_robot_maps error 999999 (unknown): "
                          "Something <id> broke")
    assert run_cli(["errors", "promote", "9999"]) == 1
