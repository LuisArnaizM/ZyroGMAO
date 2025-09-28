/**
 * Cliente HTTP base para la API de Gestión de Mantenimiento Industrial
 */

import { TokenResponse, HTTPValidationError } from '@/types';

export interface ApiClientConfig {
  baseURL: string;
  timeout?: number;
  defaultHeaders?: Record<string, string>;
}

export interface RequestConfig {
  headers?: Record<string, string>;
  timeout?: number;
  signal?: AbortSignal;
}

export class ApiError extends Error {
  constructor(
    public status: number,
    public message: string,
    public data?: unknown
  ) {
    super(message);
    this.name = 'ApiError';
  }
}

export class ValidationError extends ApiError {
  constructor(
    public status: number,
    public message: string,
    public validationErrors: HTTPValidationError
  ) {
    super(status, message, validationErrors);
    this.name = 'ValidationError';
  }
}

export class ApiClient {
  private baseURL: string;
  private timeout: number;
  private defaultHeaders: Record<string, string>;
  private accessToken: string | null = null;
  private refreshToken: string | null = null;
  private tokenExpiresAt: number | null = null;
  private isRefreshing: boolean = false;
  private refreshPromise: Promise<TokenResponse> | null = null;

  constructor(config: ApiClientConfig) {
    this.baseURL = config.baseURL.replace(/\/$/, '');
    this.timeout = config.timeout || 30000;
    this.defaultHeaders = {
      'Content-Type': 'application/json',
      ...config.defaultHeaders,
    };
  }

  /**
   * Establece los tokens de autenticación
   */
  setTokens(accessToken: string, refreshToken?: string, expires_in?: number) {
    this.accessToken = accessToken;
    if (refreshToken) {
      this.refreshToken = refreshToken;
    }
    if (expires_in) {
      this.tokenExpiresAt = Date.now() + ((expires_in - 200) * 1000);
      localStorage.setItem('token_expires_at', this.tokenExpiresAt.toString());
    }
  }

  /**
   * Limpia los tokens de autenticación
   */
  clearTokens() {
    this.accessToken = null;
    this.refreshToken = null;
    this.tokenExpiresAt = null;
    localStorage.removeItem('token_expires_at');
  }

  /**
   * Verifica si el token está próximo a expirar
   */
  private isTokenExpiring(): boolean {
    if (!this.tokenExpiresAt) return false;
    return Date.now() >= this.tokenExpiresAt;
  }

    /**
   * Verifica y renueva el token si es necesario antes de hacer la petición
   */
  private async ensureValidToken(): Promise<void> {
    if (this.isTokenExpiring() && this.refreshToken) {
      await this.refreshAccessToken();
    }
  }


  /**
   * Obtiene los headers para la petición
   */
  private getHeaders(config?: RequestConfig): Record<string, string> {
    const headers = { ...this.defaultHeaders, ...config?.headers };
    
    if (this.accessToken) {
      headers.Authorization = `Bearer ${this.accessToken}`;
    }

    return headers;
  }
  private async refreshAccessToken(): Promise<TokenResponse> {
    if (!this.refreshToken) {
      throw new ApiError(401, 'No refresh token available');
    }

    // Si ya hay un refresh en proceso, esperar a que termine
    if (this.isRefreshing && this.refreshPromise) {
      return this.refreshPromise;
    }

    this.isRefreshing = true;
    this.refreshPromise = this.performRefresh();

    try {
      return await this.refreshPromise;
    } finally {
      this.isRefreshing = false;
      this.refreshPromise = null;
    }
  }
  
  private async performRefresh(): Promise<TokenResponse> {
    try {
      // Hacer la petición de refresh sin usar el access token actual
      const response = await fetch(`${this.baseURL}/auth/refresh`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          refresh_token: this.refreshToken,
        }),
      });

      if (!response.ok) {
        throw new ApiError(response.status, 'Failed to refresh token');
      }

      const tokenResponse: TokenResponse = await response.json();
      
      // Actualizar tokens
      this.setTokens(
        tokenResponse.access_token, 
        tokenResponse.refresh_token,
        tokenResponse.expires_in
      );
      
      // Actualizar localStorage
      localStorage.setItem('access_token', tokenResponse.access_token);
      if (tokenResponse.refresh_token) {
        localStorage.setItem('refresh_token', tokenResponse.refresh_token);
      }

      return tokenResponse;
    } catch (error) {
      // Si falla el refresh, limpiar tokens y redirigir al login
      this.clearTokens();
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
      localStorage.removeItem('user_data');
      
      // Redirigir al login
      if (typeof window !== 'undefined') {
        window.location.href = '/login';
      }
      
      throw error;
    }
  }
  /**
   * Realiza una petición HTTP
   */
  private async request<T>(
    method: string,
    endpoint: string,
    data?: unknown,
    config?: RequestConfig,
    isRetry: boolean = false
  ): Promise<T> {
    if (!isRetry) {
      await this.ensureValidToken();
    }
    const url = `${this.baseURL}${endpoint}`;
    const headers = this.getHeaders(config);

    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), config?.timeout || this.timeout);

    try {
      const response = await fetch(url, {
        method,
        headers,
        body: data ? JSON.stringify(data) : undefined,
        signal: config?.signal || controller.signal,
      });

      clearTimeout(timeoutId);

      if (response.status === 401 && !isRetry && this.refreshToken) {
        try {
          await this.refreshAccessToken();
          return this.request<T>(method, endpoint, data, config, true);
        } catch (refreshError) {
          throw new ApiError(401, 'Authentication failed', refreshError);
        }
      }
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        
        if (response.status === 422) {
          throw new ValidationError(response.status, 'Validation Error', errorData);
        }
        
        throw new ApiError(
          response.status,
          errorData.message || response.statusText,
          errorData
        );
      }

      // Handle empty responses
      const contentType = response.headers.get('content-type');
      if (contentType && contentType.includes('application/json')) {
        return await response.json();
      }
      
      return {} as T;
    } catch (error) {
      clearTimeout(timeoutId);
      
      if (error instanceof ApiError || error instanceof ValidationError) {
        throw error;
      }
      
      if (error instanceof Error && error.name === 'AbortError') {
        throw new ApiError(0, 'Request timeout');
      }
      
      throw new ApiError(0, 'Network error', error);
    }
  }

  /**
   * Petición GET
   */
  async get<T>(endpoint: string, config?: RequestConfig): Promise<T> {
    return this.request<T>('GET', endpoint, undefined, config);
  }

  /**
   * Petición POST
   */
  async post<T>(endpoint: string, data?: unknown, config?: RequestConfig): Promise<T> {
    return this.request<T>('POST', endpoint, data, config);
  }

  /**
   * Petición PUT
   */
  async put<T>(endpoint: string, data?: unknown, config?: RequestConfig): Promise<T> {
    return this.request<T>('PUT', endpoint, data, config);
  }

  /**
   * Petición DELETE
   */
  async delete<T>(endpoint: string, config?: RequestConfig): Promise<T> {
    return this.request<T>('DELETE', endpoint, undefined, config);
  }

  /**
   * Petición PATCH
   */
  async patch<T>(endpoint: string, data?: unknown, config?: RequestConfig): Promise<T> {
    return this.request<T>('PATCH', endpoint, data, config);
  }

  /**
   * Petición para login (form-encoded)
   */
  async postForm<T>(endpoint: string, data: Record<string, string>, config?: RequestConfig): Promise<T> {
    const formData = new URLSearchParams(data);
    const headers = {
      ...this.getHeaders(config),
      'Content-Type': 'application/x-www-form-urlencoded',
    };

    const url = `${this.baseURL}${endpoint}`;
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), config?.timeout || this.timeout);

    try {
      const response = await fetch(url, {
        method: 'POST',
        headers,
        body: formData,
        signal: config?.signal || controller.signal,
      });

      clearTimeout(timeoutId);

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new ApiError(response.status, errorData.message || response.statusText, errorData);
      }

      return await response.json();
    } catch (error) {
      clearTimeout(timeoutId);
      
      if (error instanceof ApiError) {
        throw error;
      }
      
      if (error instanceof Error && error.name === 'AbortError') {
        throw new ApiError(0, 'Request timeout');
      }
      
      throw new ApiError(0, 'Network error', error);
    }
  }
}

/**
 * Instancia global del cliente API
 */
export const apiClient = new ApiClient({
  baseURL: 'http://localhost:8000/v1',
  timeout: 30000,
});
