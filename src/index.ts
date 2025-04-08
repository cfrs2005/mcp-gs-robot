import { mcpGSRobotService } from './services';
import { config } from './config';

// 导出所有类型定义
export * from './types';

// MCP插件接口
export const MCPGSRobot = {
  /**
   * 初始化服务
   * @param options 配置选项
   */
  init(options?: {
    clientId?: string;
    clientSecret?: string;
    openAccessKey?: string;
    apiBaseUrl?: string;
  }) {
    // 使用传入的配置或环境变量
    const clientId = options?.clientId || config.gs.clientId;
    const clientSecret = options?.clientSecret || config.gs.clientSecret;
    const openAccessKey = options?.openAccessKey || config.gs.openAccessKey;
    const apiBaseUrl = options?.apiBaseUrl || config.gs.apiBaseUrl;

    if (!clientId || !clientSecret || !openAccessKey) {
      throw new Error('缺少必要的配置参数');
    }

    return mcpGSRobotService;
  },

  /**
   * 获取机器人列表
   */
  async listRobots(params?: {
    page?: number;
    pageSize?: number;
    relation?: string;
  }) {
    return mcpGSRobotService.listRobots(params);
  },

  /**
   * 获取机器人状态
   */
  async getRobotStatus(serialNumber: string) {
    return mcpGSRobotService.getRobotStatus(serialNumber);
  },

  /**
   * 发送导航指令
   */
  async sendNavigationCommand(serialNumber: string, command: {
    type: 'CROSS_NAVIGATE' | 'PAUSE_NAVIGATE' | 'RESUME_NAVIGATE' | 'STOP_NAVIGATE';
    map?: string;
    position?: string;
  }) {
    return mcpGSRobotService.sendNavigationCommand(serialNumber, command);
  },

  /**
   * 发送任务指令
   */
  async sendTaskCommand(serialNumber: string, command: {
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
  }) {
    return mcpGSRobotService.sendTaskCommand(serialNumber, command);
  },

  /**
   * 发送远程控制指令
   */
  async sendRemoteControlCommand(serialNumber: string, command: {
    type: 'REMOTE_CONTROL_START' | 'REMOTE_CONTROL_STOP';
  }) {
    return mcpGSRobotService.sendRemoteControlCommand(serialNumber, command);
  }
}; 