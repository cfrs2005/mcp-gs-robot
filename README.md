# MCP GS Robot

高仙机器人 MCP (Model Control Protocol) 插件，用于控制高仙清洁机器人。

## 功能特性

- 支持获取机器人列表
- 支持获取机器人状态
- 支持发送导航指令
- 支持发送任务指令
- 支持发送远程控制指令

## 配置方法

在 `~/.cursor/mcp.json` 中添加以下配置：

```json
{
  "mcp-gs-robot": {
    "command": "npx",
    "args": [
      "-y",
      "@mcp-gs-robot/mcp-server-gs-robot"
    ],
    "env": {
      "GS_CLIENT_ID": "your-client-id",
      "GS_CLIENT_SECRET": "your-client-secret",
      "GS_OPEN_ACCESS_KEY": "your-open-access-key",
      "GS_API_BASE_URL": "https://openapi.gs-robot.com"
    }
  }
}
```

## 使用方法

在 Cursor 中，可以直接使用以下命令：

```typescript
// 获取机器人列表
@mcp-gs-robot listRobots

// 获取机器人状态
@mcp-gs-robot getRobotStatus "robot-serial-number"

// 发送导航指令
@mcp-gs-robot sendNavigationCommand "robot-serial" {
  "type": "CROSS_NAVIGATE",
  "map": "9-2",
  "position": "Cd"
}

// 发送任务指令
@mcp-gs-robot sendTaskCommand "robot-serial" {
  "type": "START_TASK",
  "taskConfig": {
    "cleaningMode": "__middle_cleaning",
    "task": {
      "name": "execute_task_q",
      "map": "9-2"
    }
  }
}

// 发送远程控制指令
@mcp-gs-robot sendRemoteControlCommand "robot-serial" {
  "type": "REMOTE_CONTROL_START"
}
```

## API 文档

### 获取机器人列表

```
@mcp-gs-robot listRobots [options]

选项：
  --page       页码，默认1
  --pageSize   每页数量，默认10
  --relation   关系类型：contract-合同客户, 空-终端客户, cugrup-集团
```

### 获取机器人状态

```
@mcp-gs-robot getRobotStatus <serialNumber>
```

### 发送导航指令

```
@mcp-gs-robot sendNavigationCommand <serialNumber> <command>

命令类型：
  - CROSS_NAVIGATE    导航到指定点位
  - PAUSE_NAVIGATE    暂停导航
  - RESUME_NAVIGATE   恢复导航
  - STOP_NAVIGATE     停止导航
```

### 发送任务指令

```
@mcp-gs-robot sendTaskCommand <serialNumber> <command>

命令类型：
  - START_TASK    开始任务
  - STOP_TASK     停止任务
  - PAUSE_TASK    暂停任务
  - RESUME_TASK   恢复任务
```

### 发送远程控制指令

```
@mcp-gs-robot sendRemoteControlCommand <serialNumber> <command>

命令类型：
  - REMOTE_CONTROL_START   开启远程控制
  - REMOTE_CONTROL_STOP    停止远程控制
```

## 开发

```bash
# 安装依赖
npm install

# 构建
npm run build

# 测试
npm test
```

## License

MIT 