/**
 * Servicio de autenticación
 */

import { apiClient } from '../utils/api-client';
import {
  LoginRequest,
  TokenResponse,
  ChangePasswordRequest,
  ForgotPasswordRequest,
  ResetPasswordRequest,
  UserRead,
  UserCreate,
  UserProfile
} from '@/types';

export class AuthService {
  /**
   * Iniciar sesión
   */
  async login(credentials: LoginRequest): Promise<TokenResponse> {
    const response = await apiClient.postForm<TokenResponse>('/auth/login', {
      grant_type: credentials.grant_type || 'password',
      username: credentials.username,
      password: credentials.password,
      scope: credentials.scope || '',
      client_id: credentials.client_id || '',
      client_secret: credentials.client_secret || '',
    });

    // Guardar tokens en el cliente
    if (response.access_token) {
      apiClient.setTokens(response.access_token, response.refresh_token);
    }

    return response;
  }

  /**
   * Cerrar sesión
   */
  async logout(): Promise<void> {
    await apiClient.post('/auth/logout');
    apiClient.clearTokens();
  }

  /**
   * Refrescar token
   */
  async refreshToken(refreshToken: string): Promise<TokenResponse> {
    const response = await apiClient.post<TokenResponse>('/auth/refresh', {
      refresh_token: refreshToken,
    });

    // Actualizar tokens en el cliente
    if (response.access_token) {
      apiClient.setTokens(response.access_token, response.refresh_token);
    }

    return response;
  }

  /**
   * Registrar nuevo usuario
   */
  async register(userData: UserCreate): Promise<UserRead> {
    return apiClient.post<UserRead>('/auth/register', userData);
  }

  /**
   * Obtener perfil del usuario actual
   */
  async getMe(): Promise<UserProfile> {
    return apiClient.get<UserProfile>('/users/me');
  }

  /**
   * Cambiar contraseña del usuario actual
   */
  async changePassword(passwordData: ChangePasswordRequest): Promise<void> {
    await apiClient.put('/auth/change-password', passwordData);
  }

  /**
   * Solicitar reset de contraseña
   */
  async forgotPassword(emailData: ForgotPasswordRequest): Promise<void> {
    await apiClient.post('/auth/forgot-password', emailData);
  }

  /**
   * Resetear contraseña con token
   */
  async resetPassword(resetData: ResetPasswordRequest): Promise<void> {
    await apiClient.post('/auth/reset-password', resetData);
  }

  /**
   * Verificar si la base de datos tiene usuarios
   */
  async checkDatabase(): Promise<{ has_users: boolean }> {
    return apiClient.get<{ has_users: boolean }>('/auth/check-db');
  }
}

// Instancia global del servicio
export const authService = new AuthService();
