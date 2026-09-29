# Claude Code + gs-robot V3

This project provides an MCP **stdio** server and an optional Agent Skill. The Skill teaches safe usage of V3 tools but does not replace the MCP server. Get your own OpenAPI credentials and keep them out of the repository and chat transcripts.

## Install and register MCP

```sh
pip install mcp-gs-robot
export GS_CLIENT_ID="<client-id>"
export GS_CLIENT_SECRET="<client-secret>"
export GS_OPEN_ACCESS_KEY="<access-key>"
claude mcp add gs-robot -- mcp-gs-robot
claude mcp list
```

Claude Code launches `mcp-gs-robot` on demand; do not run a second stdio instance in the same terminal. The `claude mcp add` form above inherits the calling environment; when launching Claude Code from a different environment, provide the same variables securely via your shell or MCP configuration. Do not put actual keys in shell history, project files or screenshots. For a local checkout instead of an installed command, register `claude mcp add gs-robot -- uv run mcp-gs-robot` from the repository root.

## Install the Skill

```sh
# From the checked-out repository root:
mkdir -p ~/.claude/skills
cp -r skills/gs-robot ~/.claude/skills/gs-robot
```

Restart Claude Code; use the `gs-robot` Skill for prompts about robot status, maps, cleaning tasks, schedules and command results. For project-scoped installation and other clients see [Skill README](https://github.com/cfrs2005/mcp-gs-robot/blob/main/skills/gs-robot/README.md). Install the MCP server **as well**; the Skill contains instructions and references but cannot call the OpenAPI itself.

## V3 tools and safety workflow

Use snake_case inputs and current names from the [registry-derived 40-tool table](https://github.com/cfrs2005/mcp-gs-robot/blob/main/README.md):

1. `list_robots` (v1alpha1 fallback) → `get_robot_status` with `{"robot_sn_list":["<SN>"]}` → `describe_work_state` if needed.
2. `get_robot_capabilities`, `list_work_modes`, `list_robot_maps`, `list_task_resources` to inspect supported modes and valid IDs.
3. With explicit approval, `create_task_definition` then `start_task`; poll `get_command_status` or `wait_for_command`. `run_cleaning_task` combines these steps and is also dangerous.
4. `list_task_reports`, `list_schedules`, `list_command_history` are read-only. `pause_task`, `stop_task`, `navigate_home`, schedule and definition mutations are dangerous and must be confirmed before use.

Command delivery is not proof of task completion; robot status can lag. Test commands on simulators/idle robots first. `GS_ENABLE_LEGACY_TOOLS=1` exposes old 0.1.x tools with `legacy_` prefixes only if needed for migration. Avoid `SAODI_AUTO_APPROVE=1` during testing.

## Troubleshooting

- Missing tools: verify `claude mcp list`, installed executable/PATH and inherited environment; the MCP server communicates over stdio, not `/api/v1`.
- 401 or missing robot: validate credential permissions and use `list_robots` before requesting status.
- Tool input error: use snake_case field names (`robot_sn`, `robot_sn_list`, `fusion_task_id`) and inspect the tool schema; do not use obsolete `_smart` names.
- For HTTP API/H5 testing instead, start `gs-robot-server` and use [the V3 testing guide](https://github.com/cfrs2005/mcp-gs-robot/blob/main/docs/TESTING_GUIDE.md).

[Architecture contract](https://github.com/cfrs2005/mcp-gs-robot/blob/main/docs/ARCHITECTURE_V3.md) · [OpenAPI V3 index](https://github.com/cfrs2005/mcp-gs-robot/blob/main/docs/apis.md) · [English README](https://github.com/cfrs2005/mcp-gs-robot/blob/main/README.md)
