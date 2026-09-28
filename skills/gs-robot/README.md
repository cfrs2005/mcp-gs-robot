# gs-robot Agent Skill 安装说明

> 免责声明：本项目是非官方、个人研究用途的开源项目，与高仙（Gausium）无隶属、认可或支持关系；使用风险自负。

本 Skill 教会 AI 助手通过 `mcp-gs-robot` MCP 工具运维高仙（Gausium）清洁机器人。适用于 Claude Code、Codex CLI、WorkBuddy。

## 前置依赖
- 已部署 `mcp-gs-robot` MCP server（`pip install mcp-gs-robot` 或本仓库 `uv sync` 后 `mcp-gs-robot`）。
- 已设置环境变量：`GS_CLIENT_ID` / `GS_CLIENT_SECRET` / `GS_OPEN_ACCESS_KEY`（必填）；`GS_BASE_URL` 等可选。详见 `SKILL.md` 前置条件与 `docs/ARCHITECTURE_V3.md §2`。

## 安装到 Claude Code

Claude Code 读取以下位置的 Skill（YAML frontmatter `name` + `description` + 正文）：

- **用户级（全局可用）**：将本目录复制到 `~/.claude/skills/gs-robot/`
- **项目级（仅当前仓库）**：复制到 `<repo>/.claude/skills/gs-robot/`

```bash
# 用户级
cp -r skills/gs-robot ~/.claude/skills/gs-robot

# 项目级（在仓库根目录执行）
mkdir -p .claude/skills
cp -r skills/gs-robot .claude/skills/gs-robot
```

同时在 Claude Code 的 MCP 配置（`~/.claude.json` 或项目 `.mcp.json`）中挂载 `mcp-gs-robot`：

```json
{
  "mcpServers": {
    "gs-robot": {
      "command": "mcp-gs-robot",
      "env": {
        "GS_CLIENT_ID": "<your_client_id>",
        "GS_CLIENT_SECRET": "<your_client_secret>",
        "GS_OPEN_ACCESS_KEY": "<your_access_key_secret>"
      }
    }
  }
}
```

重启 Claude Code，新会话中提及「高仙机器人」「GS…-…」「清扫任务」即可触发本 Skill。

## 安装到 Codex CLI

Codex CLI 的 Skill 目录为 `~/.codex/skills/`：

```bash
mkdir -p ~/.codex/skills
cp -r skills/gs-robot ~/.codex/skills/gs-robot
```

Codex 的 MCP 配置在 `~/.codex/config.toml`（或对应配置文件），按 Codex 文档添加 `mcp-gs-robot` server 条目，注入与上文相同的环境变量。

## 安装到 WorkBuddy

WorkBuddy 读取 `~/.workbuddy-ai/skills/` 下的 Skill：

```bash
mkdir -p ~/.workbuddy-ai/skills
cp -r skills/gs-robot ~/.workbuddy-ai/skills/gs-robot
```

WorkBuddy 的 MCP server 配置按其设置页说明挂载 `mcp-gs-robot`，并注入环境变量。

## 验证安装
1. 重启宿主，新开会话。
2. 问一句：「帮我查一下高仙机器人 <SN> 的状态」。
3. 若 Skill 生效，助手会调用 `get_robot_status`（或先 `list_robots`）并按 `SKILL.md` 输出规范回表格。
4. 若工具未出现，检查 MCP server 是否启动成功（`mcp-gs-robot` 进程 / 日志）与环境变量是否注入。

## 目录结构
```
skills/gs-robot/
├── SKILL.md                  # 主 Skill 文件（YAML frontmatter + 正文）
├── README.md                 # 本文件
└── references/
    ├── tools.md              # 全工具速查表（名称/用途/必填参数/dangerous/V3 端点）
    ├── work-states.md        # workState 码表 + 运维含义/建议动作
    ├── error-codes.md        # 任务启动失败错误码 + 常见 HTTP/OAuth 错误
    └── workflows.md          # 3 个端到端示例对话脚本
```

## 维护
- 工具名与端点契约唯一来源为 `docs/ARCHITECTURE_V3.md §3`；若仓库升级工具集，先更新该文件，再同步 `references/tools.md`。
- workState / 错误码表分别跟随 https://developer.gs-robot.com/v3docs/en_US/Robot%20Work%20State%20Reference 与 `task-startup-failure-error-codes.md`。
- 不要在 Skill 文件中写入真实凭据；示例一律用占位符。
