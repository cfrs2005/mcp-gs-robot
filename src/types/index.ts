// GS-Robot API 配置类型
export interface GSAuthConfig {
  clientId: string;
  clientSecret: string;
  openAccessKey: string;
  grantType: string;
  apiBaseUrl: string;
}

// Token信息类型
export interface TokenInfo {
  accessToken: string;
  expiresAt: number;
}

// MCP服务配置类型
export interface MCPServiceConfig {
  clientId: string;
  clientSecret: string;
  openAccessKey: string;
  apiBaseUrl?: string;
}

// 获取机器人列表的参数类型
export interface ListRobotsParams {
  page?: number;        // 页码，默认1
  pageSize?: number;    // 每页数量，默认10
  relation?: string;    // 关系类型：contract-合同客户, 空-终端客户, cugrup-集团
}

// 机器人信息类型
export interface RobotInfo {
  serialNumber: string;
  name: string;
  displayName: string;
  modelFamilyCode: string;
  modelTypeCode: string;
  online: boolean;
}

// 机器人状态类型
export interface RobotStatus {
  robotId: string;
  status: string;
  battery: number;
  position?: {
    x: number;
    y: number;
    angle: number;
  };
  taskState?: string;
  // 其他状态字段
}

// 任务配置类型
export interface TaskConfig {
  robotId: string;
  taskType: string;
  parameters: Record<string, any>;
}

// API响应类型
export interface APIResponse<T> {
  code: number;
  message: string;
  data: T;
} 