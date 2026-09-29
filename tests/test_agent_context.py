"""Saodi cognition layers, legacy-name compatibility and CLI context dump."""

import logging
import tomllib
from pathlib import Path

import pytest

from gs_openapi.agent import prompts, settings
from gs_openapi.agent.cli import legacy_main, main
from gs_openapi.agent.core import SaodiAgent
from gs_openapi.agent.providers.base import MessageEnd, TextDelta
from gs_openapi.agent.session import AgentSession
from gs_openapi.agent.settings import AgentSettings

ROOT = Path(__file__).resolve().parents[1]
ENV_NAMES = [*settings.LEGACY_ENV, *settings.LEGACY_ENV.values(),
             "SAODI_CONTEXT_DIR", "SAODI_CONTEXT_MAX_CHARS"]


@pytest.fixture(autouse=True)
def clean_env(monkeypatch):
    # app.py's load_dotenv() may have copied a developer .env into os.environ.
    for name in ENV_NAMES:
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setattr(settings, "_warned", set())


def markers(prompt: str) -> list[str]:
    return [line for line in prompt.splitlines() if line.startswith("<!-- ")]


def test_layers_load_in_order_from_skill_single_source():
    prompt = prompts.build_system_prompt()
    assert markers(prompt) == [
        "<!-- soul: soul.md -->",
        "<!-- knowledge: references/domain.md -->",
        "<!-- knowledge: SKILL.md -->",
        "<!-- knowledge: references/work-states.md -->",
        "<!-- memory: references/experience.md -->",
    ]
    assert prompt.startswith("<!-- soul: soul.md -->\n# Saodi (扫地僧)")
    assert "reply in the user's language" in prompt.lower()
    assert "110003" in prompt and "230003" in prompt
    # The official error-code table is looked up on demand, not resident.
    assert "2111000005" not in prompt and "lookup_error_code" in prompt
    assert "name: gs-robot" not in prompt  # SKILL.md frontmatter stripped
    assert prompts.find_skill_dir() == ROOT / "skills" / "gs-robot"
    assert len(prompt) <= prompts.DEFAULT_MAX_CHARS


def test_logs_file_names_and_sizes_not_content(caplog):
    with caplog.at_level(logging.INFO, logger="gs_openapi.agent.prompts"):
        prompts.build_system_prompt()
    text = caplog.text
    assert "soul:soul.md(" in text and "memory:references/experience.md(" in text
    assert "bytes" in text
    assert "Operate only the robot the user explicitly named" not in text


def test_truncation_caps_length_and_warns_with_file_names(caplog):
    full = prompts.build_system_prompt(max_chars=10**9)
    limit = full.index("<!-- knowledge: SKILL.md -->") + 50
    with caplog.at_level(logging.WARNING, logger="gs_openapi.agent.prompts"):
        prompt = prompts.build_system_prompt(max_chars=limit)
    assert len(prompt) == limit
    assert full.startswith(prompt)
    warning = next(r.getMessage() for r in caplog.records if r.levelno == logging.WARNING)
    assert "knowledge:SKILL.md" in warning
    assert "memory:references/experience.md" in warning  # listed as dropped
    assert "experience.md -->" not in prompt


def test_private_context_dir_appended_sorted_md_only(tmp_path, monkeypatch):
    (tmp_path / "b.md").write_text("私有经验 B", encoding="utf-8")
    (tmp_path / "a.md").write_text("私有经验 A", encoding="utf-8")
    (tmp_path / "ignored.txt").write_text("不应加载", encoding="utf-8")
    monkeypatch.setenv("SAODI_CONTEXT_DIR", str(tmp_path))
    prompt = prompts.build_system_prompt()
    assert markers(prompt)[-3:] == [
        "<!-- memory: references/experience.md -->",
        "<!-- private: a.md -->",
        "<!-- private: b.md -->",
    ]
    assert prompt.endswith("私有经验 B") and "不应加载" not in prompt


def test_missing_skill_dir_keeps_soul(monkeypatch, tmp_path, caplog):
    monkeypatch.setattr(prompts, "SKILL_DIRS", (tmp_path / "nope",))
    with caplog.at_level(logging.WARNING, logger="gs_openapi.agent.prompts"):
        prompt = prompts.build_system_prompt()
    assert markers(prompt) == ["<!-- soul: soul.md -->"]
    assert "Knowledge/Memory 未加载" in caplog.text


def test_installed_skill_dir_takes_precedence(monkeypatch, tmp_path):
    packaged = tmp_path / "_skills" / "gs-robot"
    (packaged / "references").mkdir(parents=True)
    (packaged / "SKILL.md").write_text("---\nname: x\n---\n打包副本", encoding="utf-8")
    monkeypatch.setattr(prompts, "SKILL_DIRS", (packaged, ROOT / "skills" / "gs-robot"))
    assert prompts.find_skill_dir() == packaged
    assert "打包副本" in prompts.build_system_prompt()


def test_legacy_env_fallback_warns_once_without_value(monkeypatch, caplog):
    monkeypatch.setenv("PI_AGENT_PROVIDER", "openai")
    monkeypatch.setenv("PI_AGENT_MAX_TURNS", "7")
    with caplog.at_level(logging.WARNING, logger="gs_openapi.agent.settings"):
        first = AgentSettings()
        AgentSettings()
    assert (first.saodi_provider, first.saodi_max_turns) == ("openai", 7)
    messages = [r.getMessage() for r in caplog.records]
    assert sum("PI_AGENT_PROVIDER" in m for m in messages) == 1
    assert sum("PI_AGENT_MAX_TURNS" in m for m in messages) == 1
    assert all("openai" not in m and "7" not in m for m in messages)  # names only, no values


def test_new_env_name_wins_over_legacy(monkeypatch, caplog):
    monkeypatch.setenv("SAODI_PROVIDER", "anthropic")
    monkeypatch.setenv("PI_AGENT_PROVIDER", "openai")
    with caplog.at_level(logging.WARNING, logger="gs_openapi.agent.settings"):
        assert AgentSettings().saodi_provider == "anthropic"
    assert "PI_AGENT_PROVIDER" not in caplog.text


def test_class_alias_and_console_scripts():
    from gs_openapi.agent import PiAgent
    from gs_openapi.agent import SaodiAgent as Exported

    assert PiAgent is SaodiAgent is Exported
    scripts = tomllib.loads((ROOT / "pyproject.toml").read_text())["project"]["scripts"]
    assert scripts["saodi"] == "gs_openapi.agent.cli:main"
    assert scripts["pi-agent"] == "gs_openapi.agent.cli:legacy_main"


def test_show_context_prints_prompt_without_llm(capsys):
    main(["--show-context"])
    out = capsys.readouterr().out
    assert out.startswith("<!-- soul: soul.md -->")


def test_pi_agent_alias_warns_then_behaves_like_saodi(monkeypatch, capsys):
    monkeypatch.setattr("sys.argv", ["pi-agent", "--show-context"])
    legacy_main()
    captured = capsys.readouterr()
    assert "pi-agent 已弃用，请改用 saodi" in captured.err
    assert captured.out.startswith("<!-- soul: soul.md -->")


async def test_system_prompt_built_once_per_session(monkeypatch):
    calls = []
    monkeypatch.setattr("gs_openapi.agent.core.build_system_prompt",
                        lambda: calls.append(1) or f"PROMPT-{len(calls)}")
    seen = []

    class Provider:
        async def stream(self, *, system, messages, tools):
            seen.append(system)
            yield TextDelta("好")
            yield MessageEnd("end_turn", {}, [{"type": "text", "text": "好"}])

    agent = SaodiAgent(None, Provider())
    first, second = AgentSession(), AgentSession()
    for session in (first, first, second):
        [event async for event in agent.run(session, "你好")]
    assert seen == ["PROMPT-1", "PROMPT-1", "PROMPT-2"]
    assert first.system_prompt == "PROMPT-1"
