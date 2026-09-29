"""Interactive terminal entry point for Pi Agent."""

import argparse
import asyncio
import json

from ..core.client import GausiumAPIClient
from ..v3.api import GausiumV3
from .core import PiAgent
from .session import AgentSession
from .settings import AgentSettings, build_provider


class TerminalConfirmGate:
    async def ask(self, session_id, confirm_id, name, input, summary) -> bool:
        answer = await asyncio.to_thread(input_fn, f"确认 {summary}? [y/N] ")
        return answer.strip().lower() in {"y", "yes"}


def input_fn(prompt: str) -> str:
    return input(prompt)


async def _repl(args: argparse.Namespace) -> None:
    overrides = {}
    if args.provider:
        overrides["pi_agent_provider"] = args.provider
    if args.model:
        overrides["pi_agent_model"] = args.model
    if args.auto_approve:
        overrides["pi_agent_auto_approve"] = True
    settings = AgentSettings(**overrides)
    provider = build_provider(settings)
    session = AgentSession()
    async with GausiumAPIClient() as client:
        agent = PiAgent(
            GausiumV3(client), provider, auto_approve=settings.pi_agent_auto_approve,
            max_turns=settings.pi_agent_max_turns, confirm_gate=TerminalConfirmGate(),
        )
        if args.robot:
            session.messages.append({"role": "user", "content": f"本次仅操作机器人 {args.robot}"})
        while True:
            try:
                user_text = await asyncio.to_thread(input_fn, "\n你> ")
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
                    print(f"\n错误: {event['message']}")
            print()


def main() -> None:
    parser = argparse.ArgumentParser(description="高仙机器人 Pi Agent 终端助手")
    parser.add_argument("--provider", choices=["anthropic", "openai"])
    parser.add_argument("--model")
    parser.add_argument("--auto-approve", action="store_true")
    parser.add_argument("--robot", help="本次会话指定的机器人 SN")
    asyncio.run(_repl(parser.parse_args()))


if __name__ == "__main__":
    main()
