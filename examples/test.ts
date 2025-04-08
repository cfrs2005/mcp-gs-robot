import { MCPGSRobotService } from '../src';
import dotenv from 'dotenv';

// 加载环境变量
dotenv.config();

async function main() {
  // 创建MCP服务实例
  const mcpService = new MCPGSRobotService({
    clientId: process.env.GS_CLIENT_ID || '',
    clientSecret: process.env.GS_CLIENT_SECRET || '',
    apiBaseUrl: process.env.GS_API_BASE_URL || ''
  });

  try {
    console.log('开始获取机器人列表...');
    const robots = await mcpService.listRobots();
    console.log('获取成功！机器人列表：', robots);
  } catch (error) {
    console.error('获取失败：', error);
  }
}

main(); 