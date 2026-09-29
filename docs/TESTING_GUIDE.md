# V3 testing guide

## Unit tests and checks

```sh
uv sync --extra dev
uv run ruff check src tests
uv run pytest -q
```

Tests use in-process ASGI requests and `httpx.MockTransport`, overriding `gs_openapi.server.deps.get_v3` and `get_agent` (see [test_server_api.py](https://github.com/cfrs2005/mcp-gs-robot/blob/main/tests/test_server_api.py)). No live Gausium or LLM credentials are needed. The server static-route tests expect a built H5 (`cd h5 && npm ci && npm run build` if missing). `uv build` packages the compiled static files.

## HTTP server with a mock upstream

For a local manual walkthrough, run your own mock HTTP server implementing the endpoints you will call: `GET /v1alpha1/robots` for robot listing, `POST /openapi/v3/robots/status/get` for status, plus `POST /gas/api/v1alpha1/oauth/token` if testing the real token manager. Set `GS_BASE_URL=http://127.0.0.1:<mock-port>/` (trailing slash), and set `GS_CLIENT_ID`, `GS_CLIENT_SECRET`, `GS_OPEN_ACCESS_KEY` to **dummy** values. These env vars redirect upstream traffic; they do not automatically create a mock backend. Match the envelope expected by the V3 client, e.g. status `{"code":0,"data":{"list":[{"robotSn":"TEST-SN","onlineStatus":"ONLINE","batteryPercent":78,"workState":0,"currentMapName":"Main"}]}}`. For an executable credential-free mocked backend, use the in-process test fixture above rather than a live server.

```sh
export GS_BASE_URL="http://127.0.0.1:<mock-port>/"
export GS_CLIENT_ID="dummy" GS_CLIENT_SECRET="dummy" GS_OPEN_ACCESS_KEY="dummy"
export GS_SERVER_API_KEY="local-test-key"
export SAODI_PROVIDER="anthropic"
export ANTHROPIC_API_KEY="dummy"  # only for health/session setup; no live chat with this value
uv run gs-robot-server
```

`GET /api/v1/health` is public. Other `/api/v1/` routes require `X-API-Key` when `GS_SERVER_API_KEY` is set. To test **chat SSE** without calling a real model, override `deps.get_agent` with a fake event generator as in `test_agent_sse_and_confirm` in the test file; `GS_BASE_URL` alone mocks only the robot API, not the LLM provider. To review the Saodi system prompt (Soul/Knowledge/Memory) without any key, run `uv run saodi --show-context`. For manual live Agent chat, supply your own valid LLM key; never send robot-motion requests on live equipment while testing.

## curl walkthrough

With the mock upstream/server above running (substitute a serial number returned by your mock):

```sh
curl http://localhost:8000/api/v1/health
curl -H 'X-API-Key: local-test-key' 'http://localhost:8000/api/v1/robots?page=1&page_size=20'
curl -H 'X-API-Key: local-test-key' -H 'Content-Type: application/json' \
  -d '{"robot_sn_list":["TEST-SN"]}' http://localhost:8000/api/v1/robots/status
curl -H 'X-API-Key: local-test-key' -H 'Content-Type: application/json' \
  -d '{"robot_sn_list":["TEST-SN"]}' http://localhost:8000/api/v1/tools/get_robot_status
curl -H 'X-API-Key: local-test-key' -H 'Content-Type: application/json' \
  -d '{}' http://localhost:8000/api/v1/agent/sessions
# Copy session_id from the previous response into the next request:
curl -N -H 'X-API-Key: local-test-key' -H 'Content-Type: application/json' \
  -d '{"content":"Describe the available tools"}' \
  'http://localhost:8000/api/v1/agent/sessions/<session_id>/messages'
```

The last request returns `data: {"type":...}` SSE lines (`text_delta`, `tool_call`, `tool_result`, `confirm_required`, `done`, `error`). It needs a valid LLM key or the test's fake agent override. If a dangerous tool emits `confirm_required`, review its arguments before sending `POST /api/v1/agent/sessions/<session_id>/confirm` with `{"confirm_id":"<id>","approve":false}` (use `true` only after deliberate approval). Direct `POST /api/v1/tools/{tool_name}` calls execute dangerous commands without Agent confirmation.

See interactive REST schemas at `http://localhost:8000/docs`. No legacy `/mcp/call` HTTP route exists.

## MCP inspector

```sh
# In the repository root with dummy credentials + a mock upstream (or real credentials in a safe environment):
npx @modelcontextprotocol/inspector uv run mcp-gs-robot
```

Use the inspector to list tool schemas, then invoke only read-only tools against the mock. MCP uses stdio; SSE above belongs to the HTTP Agent. Never paste credentials into screenshots or logs.
