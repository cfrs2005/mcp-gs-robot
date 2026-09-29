# Agent setup prompt

Copy one of the prompts below into Claude Code, Codex or Cursor (agent mode) inside an empty working directory. The agent clones and installs mcp-gs-robot, asks you for credentials and writes them only into `.env`, runs the tests, builds the H5, starts `gs-robot-server`, checks `/api/v1/health`, walks you through entering the API key in the H5 Settings page, and smoke-tests with **read-only tools only** (`list_robots`, `get_robot_status`). It never calls a dangerous tool.

The same English prompt is embedded in [README.md](../README.md#-let-your-ai-agent-set-it-up); the Chinese one in [README_CN.md](../README_CN.md#-让-ai-agent-帮你装).

## English

```text
Set up mcp-gs-robot (an unofficial MCP / REST / agent wrapper for the Gausium OpenAPI V3) on this
machine. Work step by step, show me each command's result, and stop at the first failure.

Hard rules
- Robots are physical machines. Call read-only tools only. Never call a tool marked dangerous
  (anything that creates, updates or deletes tasks or schedules, starts / pauses / resumes / stops /
  skips tasks, navigates, runs a cleaning workflow, or writes memory with `remember`).
- Never print, echo, log or commit credentials. Write them only into .env with your file-edit tool
  (not via shell echo), never paste them back to me, and confirm .env is git-ignored.

Steps
1. Prerequisites: `python3 --version` (3.12+) and `uv --version`. `node --version` (18+) only
   matters for step 5.
2. `git clone https://github.com/cfrs2005/mcp-gs-robot.git && cd mcp-gs-robot && uv sync --extra dev`
3. `cp .env.example .env`. Ask me for GS_CLIENT_ID, GS_CLIENT_SECRET and GS_OPEN_ACCESS_KEY (the
   AccessKeySecret, not the AccessKeyID), and whether to use production
   (https://openapi.gs-robot.com/) or test (https://openapi.dev.gs-robot.com/) for GS_BASE_URL.
   Ask which LLM provider I use: Anthropic (SAODI_PROVIDER=anthropic + ANTHROPIC_API_KEY) or an
   OpenAI-compatible endpoint (SAODI_PROVIDER=openai + OPENAI_BASE_URL + OPENAI_API_KEY +
   SAODI_MODEL). Generate GS_SERVER_API_KEY yourself with
   `python3 -c "import re,secrets,pathlib;p=pathlib.Path('.env');p.write_text(re.sub(r'(?m)^GS_SERVER_API_KEY=.*$','GS_SERVER_API_KEY='+secrets.token_urlsafe(32),p.read_text()))"` (it rewrites the line in .env in place and never prints the key; I will read it from .env myself).
   Then run `git check-ignore .env` (it must print .env) and `git status --short` (.env must not
   appear).
4. `uv run pytest -q` and `uv run ruff check src tests`; both must pass.
5. If Node 18+ is available: `cd h5 && npm ci && npm run build && cd ..`. Otherwise skip; a
   prebuilt H5 is already in src/gs_openapi/server/static/.
6. Start the server in the background with its output in a log file:
   `uv run gs-robot-server > server.log 2>&1 &`
7. `curl -s http://127.0.0.1:8000/api/v1/health` must return "status":"ok" and
   "auth_required":true.
8. Tell me to open http://localhost:8000/, go to Settings, paste the GS_SERVER_API_KEY value from
   .env and press Save (it should report the connection as OK). Do not show me the key yourself.
9. Read-only smoke test. Load the key without printing it:
   `KEY=$(grep '^GS_SERVER_API_KEY=' .env | cut -d= -f2-)`
   - `curl -s -X POST -H "X-API-Key: $KEY" -H 'Content-Type: application/json'
     -d '{"page":1,"page_size":5}' http://127.0.0.1:8000/api/v1/tools/list_robots`
   - pick one robot from that list with "online": true and call get_robot_status the same way
     with body {"robot_sn_list":["<that SN>"]}.
   Error meanings: 401 = wrong or missing X-API-Key; 110003 = these credentials are not bound to
   that robot (not "no data"); 230003 = robot offline; 100026 = rate limited, slow down.
10. Report: tool versions, pytest / ruff results, the health response, how many robots are
    online / offline, and any error as `<code> <msg>`. Leave out secrets and trace IDs.
```

## 中文

```text
在这台机器上安装并配置 mcp-gs-robot（高仙 OpenAPI V3 的非官方 MCP / REST / Agent 封装）。
一步一步做，每条命令都把结果给我看，遇到第一个失败就停下。

硬性规则
- 机器人是实体机器。只调用只读工具。绝不调用任何标记为 dangerous 的工具（创建、修改、删除任务或排班，
  启动 / 暂停 / 继续 / 停止 / 跳过任务，导航，组合清洁流程，以及用 `remember` 写记忆）。
- 绝不打印、回显、记录或提交任何凭证。凭证只用文件编辑工具写进 .env（不要用 shell echo），不要把它们
  复述给我，并确认 .env 已被 git 忽略。

步骤
1. 前置条件：`python3 --version`（3.12+）和 `uv --version`。`node --version`（18+）只影响第 5 步。
2. `git clone https://github.com/cfrs2005/mcp-gs-robot.git && cd mcp-gs-robot && uv sync --extra dev`
3. `cp .env.example .env`。向我要 GS_CLIENT_ID、GS_CLIENT_SECRET、GS_OPEN_ACCESS_KEY（填 AccessKeySecret，
   不是 AccessKeyID），并问我 GS_BASE_URL 用生产（https://openapi.gs-robot.com/）还是测试
   （https://openapi.dev.gs-robot.com/）。再问我用哪个 LLM：Anthropic（SAODI_PROVIDER=anthropic +
   ANTHROPIC_API_KEY）或 OpenAI 兼容端点（SAODI_PROVIDER=openai + OPENAI_BASE_URL + OPENAI_API_KEY +
   SAODI_MODEL）。GS_SERVER_API_KEY 由你用
   `python3 -c "import re,secrets,pathlib;p=pathlib.Path('.env');p.write_text(re.sub(r'(?m)^GS_SERVER_API_KEY=.*$','GS_SERVER_API_KEY='+secrets.token_urlsafe(32),p.read_text()))"` 原地写进 .env（不回显 key，我自己去 .env 里看）。
   然后跑 `git check-ignore .env`（必须输出 .env）和 `git status --short`（不能出现 .env）。
4. `uv run pytest -q` 和 `uv run ruff check src tests`，两者都必须通过。
5. 有 Node 18+ 时：`cd h5 && npm ci && npm run build && cd ..`；没有就跳过，
   src/gs_openapi/server/static/ 里已经有预构建的 H5。
6. 后台启动服务，输出写进日志文件：`uv run gs-robot-server > server.log 2>&1 &`
7. `curl -s http://127.0.0.1:8000/api/v1/health` 必须返回 "status":"ok" 和 "auth_required":true。
8. 让我打开 http://localhost:8000/，进入「设置」，粘贴 .env 里 GS_SERVER_API_KEY 的值并保存（应提示连接成功）。
   你自己不要把 key 显示给我。
9. 只读冒烟测试。读取 key 但不打印：
   `KEY=$(grep '^GS_SERVER_API_KEY=' .env | cut -d= -f2-)`
   - `curl -s -X POST -H "X-API-Key: $KEY" -H 'Content-Type: application/json'
     -d '{"page":1,"page_size":5}' http://127.0.0.1:8000/api/v1/tools/list_robots`
   - 从列表里挑一台 "online": true 的机器人，用同样方式调 get_robot_status，
     body 为 {"robot_sn_list":["<该 SN>"]}。
   错误含义：401 = X-API-Key 缺失或错误；110003 = 当前凭证没有绑定这台机器人（不是「没有数据」）；
   230003 = 机器人离线；100026 = 限流，放慢速度。
10. 汇报：工具版本、pytest / ruff 结果、health 响应、在线 / 离线机器人数量，以及遇到的错误（格式 `<码> <msg>`）。
    不要包含任何密钥和 trace ID。
```
