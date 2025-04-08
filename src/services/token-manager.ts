import axios, { AxiosError } from 'axios';
import { GSAuthConfig, TokenInfo } from '../types';

export class TokenManager {
  private tokenInfo: TokenInfo | null = null;
  private readonly config: GSAuthConfig;
  private readonly maxRetries = 3;
  private readonly retryDelay = 1000; // 1秒

  constructor(config: GSAuthConfig) {
    this.config = config;
  }

  async getToken(): Promise<string> {
    if (!this.tokenInfo || Date.now() >= this.tokenInfo.expiresAt) {
      this.tokenInfo = await this.fetchNewTokenWithRetry();
    }
    return this.tokenInfo.accessToken;
  }

  private async delay(ms: number): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, ms));
  }

  private async fetchNewTokenWithRetry(): Promise<TokenInfo> {
    let lastError: Error | null = null;
    
    for (let attempt = 1; attempt <= this.maxRetries; attempt++) {
      try {
        console.log(`尝试获取token (第${attempt}次)...`);
        return await this.fetchNewToken();
      } catch (error) {
        lastError = error as Error;
        console.error(`第${attempt}次获取token失败:`, error);
        
        if (attempt < this.maxRetries) {
          const delayTime = this.retryDelay * attempt;
          console.log(`等待${delayTime}ms后重试...`);
          await this.delay(delayTime);
        }
      }
    }

    throw lastError || new Error('获取token失败，已达到最大重试次数');
  }

  private async fetchNewToken(): Promise<TokenInfo> {
    try {
      console.log('开始获取token...');
      const tokenUrl = `${this.config.apiBaseUrl}/gas/api/v1alpha1/oauth/token`;
      console.log('请求URL:', tokenUrl);
      
      const instance = axios.create({
        timeout: 30000,
        maxContentLength: Infinity,
        maxBodyLength: Infinity,
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json'
        }
      });

      const response = await instance.post(
        tokenUrl,
        {
          grant_type: "urn:gaussian:params:oauth:grant-type:open-access-token",
          client_id: this.config.clientId,
          client_secret: this.config.clientSecret,
          open_access_key: this.config.openAccessKey
        }
      );

      console.log('Token响应:', JSON.stringify(response.data, null, 2));

      // 根据截图中的响应格式修改
      const accessToken = response.data.access_token;
      const expiresIn = response.data.expires_in || (24 * 60 * 60); // 默认24小时
      const expiresAt = Date.now() + (expiresIn * 1000);

      return {
        accessToken,
        expiresAt
      };
    } catch (error) {
      if (axios.isAxiosError(error)) {
        const axiosError = error as AxiosError;
        console.error('请求详情:', {
          url: axiosError.config?.url,
          method: axiosError.config?.method,
          headers: axiosError.config?.headers,
          data: axiosError.config?.data
        });
        console.error('响应详情:', {
          status: axiosError.response?.status,
          statusText: axiosError.response?.statusText,
          data: axiosError.response?.data
        });
        throw new Error(`获取token失败: ${axiosError.message}, 响应: ${JSON.stringify(axiosError.response?.data)}`);
      }
      throw error;
    }
  }
} 