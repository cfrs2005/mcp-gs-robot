import axios, { AxiosInstance } from 'axios';
import { MCPServiceConfig, RobotStatus, TaskConfig, RobotInfo, ListRobotsParams } from '../types';
import { TokenManager } from './token-manager';

export class MCPGSRobotService {
  private readonly tokenManager: TokenManager;
  private readonly apiClient: AxiosInstance;
  private readonly apiBaseUrl: string;

  constructor(config: MCPServiceConfig) {
    this.apiBaseUrl = config.apiBaseUrl || 'https://openapi.gs-robot.com';
    
    this.tokenManager = new TokenManager({
      clientId: config.clientId,
      clientSecret: config.clientSecret,
      openAccessKey: config.openAccessKey,
      grantType: "urn:gaussian:params:oauth:grant-type:open-access-token",
      apiBaseUrl: this.apiBaseUrl
    });

    this.apiClient = axios.create({
      baseURL: this.apiBaseUrl,
      timeout: 30000,
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json'
      },
      maxContentLength: Infinity,
      maxBodyLength: Infinity
    });

    // 请求拦截器：自动添加token
    this.apiClient.interceptors.request.use(async (config) => {
      const token = await this.tokenManager.getToken();
      if (config.headers) {
        config.headers.Authorization = `Bearer ${token}`;
      }
      return config;
    });

    // 响应拦截器：处理错误
    this.apiClient.interceptors.response.use(
      (response) => response,
      (error) => {
        console.error('请求失败:', {
          url: error.config?.url,
          method: error.config?.method,
          status: error.response?.status,
          statusText: error.response?.statusText,
          data: error.response?.data
        });
        return Promise.reject(error);
      }
    );
  }

  /**
   * 获取机器人状态
   */
  async getRobotStatus(robotId: string): Promise<RobotStatus> {
    try {
      const response = await this.apiClient.get(`/openapi/v1alpha1/robots/${robotId}/status`);
      
      if (response.data.code !== 0) {
        throw new Error(`获取机器人状态失败: ${response.data.message}`);
      }

      return {
        robotId,
        status: response.data.data.status,
        battery: response.data.data.battery,
        position: response.data.data.position,
        taskState: response.data.data.taskState
      };
    } catch (error) {
      if (axios.isAxiosError(error)) {
        throw new Error(`获取机器人状态失败: ${error.message}`);
      }
      throw error;
    }
  }

  /**
   * 获取机器人列表
   * @param params 查询参数
   * @returns 机器人列表
   */
  async listRobots(params: ListRobotsParams = {}): Promise<RobotInfo[]> {
    try {
      console.log('开始获取机器人列表...');
      const response = await this.apiClient.get('/v1alpha1/robots', {
        params: {
          page: params.page || 1,
          pageSize: params.pageSize || 10,
          relation: params.relation || ''  // contract: 合同客户, 空: 终端客户, cugrup: 集团
        }
      });
      
      console.log('获取机器人列表响应:', JSON.stringify(response.data, null, 2));

      // 直接返回robots数组，不再检查code
      return response.data.robots || [];
    } catch (error) {
      if (axios.isAxiosError(error)) {
        throw new Error(`获取机器人列表失败: ${error.message}, 响应: ${JSON.stringify(error.response?.data)}`);
      }
      throw error;
    }
  }

  /**
   * 下发任务
   */
  async submitTask(taskConfig: TaskConfig): Promise<string> {
    try {
      const response = await this.apiClient.post(
        `/openapi/v2alpha1/site/submitTask`,
        taskConfig
      );

      if (response.data.code !== 0) {
        throw new Error(`任务下发失败: ${response.data.message}`);
      }

      return response.data.data.taskId;
    } catch (error) {
      if (axios.isAxiosError(error)) {
        throw new Error(`任务下发失败: ${error.message}`);
      }
      throw error;
    }
  }

  /**
   * 发送导航指令
   */
  async sendNavigationCommand(serialNumber: string, command: {
    type: 'CROSS_NAVIGATE' | 'PAUSE_NAVIGATE' | 'RESUME_NAVIGATE' | 'STOP_NAVIGATE';
    map?: string;
    position?: string;
  }) {
    try {
      const response = await this.apiClient.post(`/v1alpha1/robots/${serialNumber}/commands`, {
        serialNumber,
        remoteNavigationCommandType: command.type,
        ...(command.map && command.position ? {
          commandParameter: {
            startNavigationParameter: {
              map: command.map,
              position: command.position
            }
          }
        } : {})
      });
      return response.data;
    } catch (error) {
      if (axios.isAxiosError(error)) {
        throw new Error(`发送导航指令失败: ${error.message}, 响应: ${JSON.stringify(error.response?.data)}`);
      }
      throw error;
    }
  }

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
    try {
      const response = await this.apiClient.post(`/v1alpha1/robots/${serialNumber}/commands`, {
        serialNumber,
        remoteTaskCommandType: command.type,
        ...(command.taskConfig ? {
          commandParameter: {
            startTaskParameter: command.taskConfig
          }
        } : {})
      });
      return response.data;
    } catch (error) {
      if (axios.isAxiosError(error)) {
        throw new Error(`发送任务指令失败: ${error.message}, 响应: ${JSON.stringify(error.response?.data)}`);
      }
      throw error;
    }
  }

  /**
   * 发送远程控制指令
   */
  async sendRemoteControlCommand(serialNumber: string, command: {
    type: 'REMOTE_CONTROL_START' | 'REMOTE_CONTROL_STOP';
  }) {
    try {
      const response = await this.apiClient.post(`/v1alpha1/robots/${serialNumber}/commands`, {
        serialNumber,
        remoteControlCommandType: command.type
      });
      return response.data;
    } catch (error) {
      if (axios.isAxiosError(error)) {
        throw new Error(`发送远程控制指令失败: ${error.message}, 响应: ${JSON.stringify(error.response?.data)}`);
      }
      throw error;
    }
  }
} 