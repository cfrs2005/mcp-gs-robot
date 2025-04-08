# MCP GS Robot

高仙机器人 MCP (Model Control Protocol) 插件，用于控制高仙清洁机器人。

## 功能特性

- 支持获取机器人列表
- 支持获取机器人状态
- 支持发送导航指令
- 支持发送任务指令
- 支持发送远程控制指令

## 安装

```bash
npm install @your-org/mcp-gs-robot
```

## 使用方法

```typescript
import { MCPGSRobot } from '@your-org/mcp-gs-robot';

// 初始化
MCPGSRobot.init({
  clientId: 'your-client-id',
  clientSecret: 'your-client-secret',
  openAccessKey: 'your-open-access-key'
});

// 获取机器人列表
const robots = await MCPGSRobot.listRobots();

// 发送导航指令
await MCPGSRobot.sendNavigationCommand('robot-serial', {
  type: 'CROSS_NAVIGATE',
  map: '9-2',
  position: 'Cd'
});
```

## 环境变量

创建 `.env` 文件并配置以下环境变量：

```bash
GS_CLIENT_ID=your-client-id
GS_CLIENT_SECRET=your-client-secret
GS_OPEN_ACCESS_KEY=your-open-access-key
GS_API_BASE_URL=https://openapi.gs-robot.com
```

## API 文档

### 初始化

```typescript
MCPGSRobot.init(options?: {
  clientId?: string;
  clientSecret?: string;
  openAccessKey?: string;
  apiBaseUrl?: string;
})
```

### 获取机器人列表

```typescript
MCPGSRobot.listRobots(params?: {
  page?: number;
  pageSize?: number;
  relation?: string;
})
```

### 获取机器人状态

```typescript
MCPGSRobot.getRobotStatus(serialNumber: string)
```

### 发送导航指令

```typescript
MCPGSRobot.sendNavigationCommand(serialNumber: string, command: {
  type: 'CROSS_NAVIGATE' | 'PAUSE_NAVIGATE' | 'RESUME_NAVIGATE' | 'STOP_NAVIGATE';
  map?: string;
  position?: string;
})
```

### 发送任务指令

```typescript
MCPGSRobot.sendTaskCommand(serialNumber: string, command: {
  type: 'START_TASK' | 'STOP_TASK' | 'PAUSE_TASK' | 'RESUME_TASK';
  taskConfig?: {
    cleaningMode?: string;
    task?: {
      name: string;
      map: string;
      loop?: boolean;
      loopCount?: number;
    };
  };
})
```

### 发送远程控制指令

```typescript
MCPGSRobot.sendRemoteControlCommand(serialNumber: string, command: {
  type: 'REMOTE_CONTROL_START' | 'REMOTE_CONTROL_STOP';
})
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