import { MCPGSRobotService } from './mcp-gs-robot';
import { config } from '../config';

// 创建单例服务实例
export const mcpGSRobotService = new MCPGSRobotService({
  clientId: config.gs.clientId,
  clientSecret: config.gs.clientSecret,
  openAccessKey: config.gs.openAccessKey,
  apiBaseUrl: config.gs.apiBaseUrl
});

// 导出服务类型
export type { MCPGSRobotService } from './mcp-gs-robot';
export type { TokenManager } from './token-manager'; 