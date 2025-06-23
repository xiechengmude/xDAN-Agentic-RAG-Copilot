/**
 * RAGFlow API客户端
 * 统一的HTTP客户端，处理请求/响应、错误处理、重试机制等
 */

export interface ApiConfig {
  baseURL: string;
  timeout?: number;
  headers?: Record<string, string>;
  retryAttempts?: number;
  retryDelay?: number;
}

export interface RequestOptions {
  headers?: Record<string, string>;
  body?: string | FormData;
  signal?: AbortSignal;
  timeout?: number;
}

export interface ApiResponse<T = any> {
  code: number;
  message: string;
  data?: T;
  meta?: {
    page?: number;
    size?: number;
    total?: number;
    has_next?: boolean;
    has_prev?: boolean;
  };
}

export enum ErrorType {
  NETWORK_ERROR = 'NETWORK_ERROR',
  API_ERROR = 'API_ERROR',
  VALIDATION_ERROR = 'VALIDATION_ERROR',
  PERMISSION_ERROR = 'PERMISSION_ERROR',
  TIMEOUT_ERROR = 'TIMEOUT_ERROR',
  UNKNOWN_ERROR = 'UNKNOWN_ERROR'
}

export class ApiError extends Error {
  public type: ErrorType;
  public code: number;
  public details?: any;

  constructor(code: number, message: string, details?: any) {
    super(message);
    this.name = 'ApiError';
    this.code = code;
    this.details = details;
    this.type = this.getErrorType(code);
  }

  private getErrorType(code: number): ErrorType {
    if (code >= 400 && code < 500) {
      if (code === 401 || code === 403) {
        return ErrorType.PERMISSION_ERROR;
      }
      if (code === 408) {
        return ErrorType.TIMEOUT_ERROR;
      }
      return ErrorType.API_ERROR;
    }
    if (code >= 500) {
      return ErrorType.API_ERROR;
    }
    return ErrorType.UNKNOWN_ERROR;
  }
}

export class ApiClient {
  private baseURL: string;
  private defaultHeaders: Record<string, string>;
  private timeout: number;
  private retryAttempts: number;
  private retryDelay: number;

  constructor(config: ApiConfig) {
    this.baseURL = config.baseURL;
    this.defaultHeaders = config.headers || {
      'Content-Type': 'application/json',
      'Accept': 'application/json',
    };
    this.timeout = config.timeout || 30000;
    this.retryAttempts = config.retryAttempts || 3;
    this.retryDelay = config.retryDelay || 1000;
  }

  /**
   * 发送HTTP请求
   */
  async request<T>(
    method: string,
    url: string,
    options: RequestOptions = {}
  ): Promise<ApiResponse<T>> {
    return this.withRetry(() => this.doRequest<T>(method, url, options));
  }

  /**
   * 执行单次请求
   */
  private async doRequest<T>(
    method: string,
    url: string,
    options: RequestOptions = {}
  ): Promise<ApiResponse<T>> {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), options.timeout || this.timeout);

    try {
      const headers = { ...this.defaultHeaders, ...options.headers };
      
      // 如果是FormData，移除Content-Type让浏览器自动设置
      if (options.body instanceof FormData) {
        delete headers['Content-Type'];
      }

      const response = await fetch(`${this.baseURL}${url}`, {
        method,
        headers,
        body: options.body,
        signal: options.signal || controller.signal,
      });

      clearTimeout(timeoutId);

      if (!response.ok) {
        const errorText = await response.text();
        throw new ApiError(response.status, errorText || response.statusText);
      }

      // 处理不同的响应类型
      const contentType = response.headers.get('content-type');
      
      if (contentType?.includes('application/json')) {
        const data = await response.json();
        return data as ApiResponse<T>;
      }
      
      if (contentType?.includes('text/')) {
        const text = await response.text();
        return { code: 0, message: 'Success', data: text as any };
      }
      
      // 对于其他类型（如文件下载），返回blob
      const blob = await response.blob();
      return { code: 0, message: 'Success', data: blob as any };

    } catch (error) {
      clearTimeout(timeoutId);
      throw this.handleError(error);
    }
  }

  /**
   * 重试机制
   */
  private async withRetry<T>(fn: () => Promise<T>): Promise<T> {
    let lastError: Error;

    for (let attempt = 1; attempt <= this.retryAttempts; attempt++) {
      try {
        return await fn();
      } catch (error) {
        lastError = error instanceof Error ? error : new Error('Unknown error');

        // 如果是客户端错误或取消请求，不重试
        if (error instanceof ApiError) {
          if (error.code >= 400 && error.code < 500) {
            throw error;
          }
        }

        if (error instanceof Error && error.name === 'AbortError') {
          throw error;
        }

        if (attempt === this.retryAttempts) {
          throw lastError;
        }

        // 指数退避
        const delay = this.retryDelay * Math.pow(2, attempt - 1);
        await new Promise(resolve => setTimeout(resolve, delay));
      }
    }

    throw lastError!;
  }

  /**
   * 错误处理
   */
  private handleError(error: unknown): ApiError {
    if (error instanceof ApiError) {
      return error;
    }

    if (error instanceof Error) {
      if (error.name === 'AbortError') {
        return new ApiError(408, '请求超时');
      }
      return new ApiError(500, error.message);
    }

    return new ApiError(500, '未知错误');
  }

  /**
   * GET请求
   */
  async get<T>(url: string, params?: Record<string, any>, options?: RequestOptions): Promise<ApiResponse<T>> {
    const queryString = params ? `?${new URLSearchParams(params).toString()}` : '';
    return this.request<T>('GET', `${url}${queryString}`, options);
  }

  /**
   * POST请求
   */
  async post<T>(url: string, data?: any, options?: RequestOptions): Promise<ApiResponse<T>> {
    const body = data instanceof FormData ? data : JSON.stringify(data);
    return this.request<T>('POST', url, { ...options, body });
  }

  /**
   * PUT请求
   */
  async put<T>(url: string, data?: any, options?: RequestOptions): Promise<ApiResponse<T>> {
    const body = data ? JSON.stringify(data) : undefined;
    return this.request<T>('PUT', url, { ...options, body });
  }

  /**
   * DELETE请求
   */
  async delete<T>(url: string, data?: any, options?: RequestOptions): Promise<ApiResponse<T>> {
    const body = data ? JSON.stringify(data) : undefined;
    return this.request<T>('DELETE', url, { ...options, body });
  }

  /**
   * 文件上传
   */
  async upload<T>(url: string, files: File[], additionalData?: Record<string, string>): Promise<ApiResponse<T>> {
    const formData = new FormData();
    
    files.forEach(file => {
      formData.append('file', file);
    });
    
    if (additionalData) {
      Object.entries(additionalData).forEach(([key, value]) => {
        formData.append(key, value);
      });
    }

    return this.post<T>(url, formData);
  }

  /**
   * 流式请求（用于SSE）
   */
  async stream(
    url: string,
    data?: any,
    callbacks?: {
      onMessage?: (data: any) => void;
      onError?: (error: Error) => void;
      onComplete?: () => void;
    }
  ): Promise<() => void> {
    const controller = new AbortController();

    try {
      const response = await fetch(`${this.baseURL}${url}`, {
        method: 'POST',
        headers: this.defaultHeaders,
        body: data ? JSON.stringify(data) : undefined,
        signal: controller.signal,
      });

      if (!response.ok) {
        throw new ApiError(response.status, await response.text());
      }

      if (!response.body) {
        throw new ApiError(500, '响应体为空');
      }

      this.processStreamResponse(response.body, callbacks);
    } catch (error) {
      callbacks?.onError?.(this.handleError(error));
    }

    return () => controller.abort();
  }

  /**
   * 处理流式响应
   */
  private async processStreamResponse(
    body: ReadableStream<Uint8Array>,
    callbacks?: {
      onMessage?: (data: any) => void;
      onError?: (error: Error) => void;
      onComplete?: () => void;
    }
  ): Promise<void> {
    const reader = body.getReader();
    const decoder = new TextDecoder();
    let buffer = '';

    try {
      while (true) {
        const { done, value } = await reader.read();

        if (done) {
          callbacks?.onComplete?.();
          break;
        }

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() || '';

        for (const line of lines) {
          if (line.startsWith('data:')) {
            try {
              const jsonData = line.slice(5).trim();
              if (jsonData) {
                const data = JSON.parse(jsonData);
                callbacks?.onMessage?.(data);
              }
            } catch (error) {
              console.error('解析SSE数据失败:', error);
            }
          }
        }
      }
    } catch (error) {
      callbacks?.onError?.(error instanceof Error ? error : new Error('Stream processing error'));
    }
  }
}

// 默认API客户端实例
export const apiClient = new ApiClient({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://150.109.16.195:7080',
  timeout: 30000,
  retryAttempts: 3,
  retryDelay: 1000,
});

// 认证管理
export class AuthManager {
  private static instance: AuthManager;
  private token: string | null = null;

  static getInstance(): AuthManager {
    if (!AuthManager.instance) {
      AuthManager.instance = new AuthManager();
    }
    return AuthManager.instance;
  }

  setToken(token: string): void {
    this.token = token;
    localStorage.setItem('ragflow_auth_token', token);
    this.updateApiClientHeaders();
  }

  getToken(): string | null {
    if (!this.token) {
      this.token = localStorage.getItem('ragflow_auth_token');
    }
    return this.token;
  }

  clearToken(): void {
    this.token = null;
    localStorage.removeItem('ragflow_auth_token');
    this.updateApiClientHeaders();
  }

  isAuthenticated(): boolean {
    return !!this.getToken();
  }

  private updateApiClientHeaders(): void {
    const token = this.getToken();
    if (token) {
      apiClient['defaultHeaders']['Authorization'] = `Bearer ${token}`;
    } else {
      delete apiClient['defaultHeaders']['Authorization'];
    }
  }
}

// 初始化认证
AuthManager.getInstance().updateApiClientHeaders();