import dotenv from 'dotenv';
import path from 'path';

// 加载环境变量
const envPath = path.resolve(process.cwd(), '.env');
const result = dotenv.config({ path: envPath });

if (result.error) {
  throw new Error(`无法加载配置文件: ${result.error.message}`);
}

// 检查必要的环境变量
const requiredEnvVars = ['GS_CLIENT_ID', 'GS_CLIENT_SECRET', 'GS_OPEN_ACCESS_KEY', 'GS_API_BASE_URL'];
const missingVars = requiredEnvVars.filter(varName => !process.env[varName]);

if (missingVars.length > 0) {
  throw new Error(`缺少必要的环境变量: ${missingVars.join(', ')}`);
}

// 导出配置
export const config = {
  gs: {
    clientId: process.env.GS_CLIENT_ID!,
    clientSecret: process.env.GS_CLIENT_SECRET!,
    openAccessKey: process.env.GS_OPEN_ACCESS_KEY!,
    apiBaseUrl: process.env.GS_API_BASE_URL || 'https://openapi.gs-robot.com'
  }
}; 