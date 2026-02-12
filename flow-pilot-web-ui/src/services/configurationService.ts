
import axios from 'axios';

const DEFAULT_API_PORT = 8000;

export interface APIConfiguration {
  baseUrl: string;
  port: number;
  timeout: number;
  retries: number;
}

export interface ServiceEndpoints {
  dataAcquisition: string;
  preprocessing: string;
  augmentation: string;
  mlProcessing: string;
  applications: string;
}

class ConfigurationService {
  private config: APIConfiguration;
  private endpoints: ServiceEndpoints;

  constructor() {
    this.config = this.loadConfiguration();
    this.endpoints = this.buildEndpoints();
  }

  private loadConfiguration(): APIConfiguration {
    return {
      baseUrl: import.meta.env.VITE_API_BASE_URL || 'http://localhost',
      port: parseInt(import.meta.env.VITE_API_PORT || DEFAULT_API_PORT.toString()),
      timeout: parseInt(import.meta.env.VITE_API_TIMEOUT || '30000'),
      retries: parseInt(import.meta.env.VITE_API_RETRIES || '3')
    };
  }

  private buildEndpoints(): ServiceEndpoints {
    const baseUrl = `${this.config.baseUrl}:${this.config.port}`;
    return {
      dataAcquisition: `${baseUrl}/m1`,
      preprocessing: `${baseUrl}/m2`,
      augmentation: `${baseUrl}/m3`,
      mlProcessing: `${baseUrl}/m4`,
      applications: `${baseUrl}/m5`
    };
  }

  public getConfiguration(): APIConfiguration {
    return { ...this.config };
  }

  public getEndpoints(): ServiceEndpoints {
    return { ...this.endpoints };
  }

  public updatePort(newPort: number): void {
    this.config.port = newPort;
    this.endpoints = this.buildEndpoints();

    // Update axios defaults
    this.configureAxios();
  }

  public updateBaseUrl(newBaseUrl: string): void {
    this.config.baseUrl = newBaseUrl;
    this.endpoints = this.buildEndpoints();

    // Update axios defaults
    this.configureAxios();
  }

  public getFullApiUrl(): string {
    return `${this.config.baseUrl}:${this.config.port}`;
  }

  private configureAxios(): void {
    axios.defaults.baseURL = this.getFullApiUrl();
    axios.defaults.timeout = this.config.timeout;

    // Add retry interceptor
    axios.interceptors.response.use(
      (response) => response,
      async (error) => {
        const config = error.config;
        if (config && config.retryCount < this.config.retries) {
          config.retryCount = config.retryCount || 0;
          config.retryCount++;

          // Wait before retrying
          await new Promise(resolve => setTimeout(resolve, 1000 * config.retryCount));

          return axios(config);
        }
        return Promise.reject(error);
      }
    );
  }

  /**
   * Test connection to the API server
   */
  public async testConnection(): Promise<{ success: boolean; latency?: number; error?: string }> {
    const startTime = Date.now();
    try {
      const response = await axios.get(`${this.getFullApiUrl()}/api/health`);
      const latency = Date.now() - startTime;

      return {
        success: response.status === 200,
        latency
      };
    } catch (error: any) {
      return {
        success: false,
        error: error.message || 'Connection failed'
      };
    }
  }

  /**
   * Get API server status and module availability
   */
  public async getServerStatus(): Promise<{ modules: Record<string, boolean>; version: string; uptime: number }> {
    const response = await axios.get(`${this.getFullApiUrl()}/api/status`);
    return response.data;
  }
}

// Singleton instance
export const configurationService = new ConfigurationService();

// Export utility functions for backward compatibility
export const getApiBaseUrl = () => configurationService.getFullApiUrl();
export const updateApiPort = (port: number) => configurationService.updatePort(port);
export const testApiConnection = () => configurationService.testConnection();
