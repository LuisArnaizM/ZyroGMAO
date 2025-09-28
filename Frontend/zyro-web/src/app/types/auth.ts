/**
 * Tipos para autenticación
 */

export interface LoginRequest {
  grant_type?: string;
  username: string;
  password: string;
  scope?: string;
  client_id?: string;
  client_secret?: string;
}

export interface ChangePasswordRequest {
  current_password: string;
  new_password: string;
}

export interface ForgotPasswordRequest {
  email: string;
  organization_slug?: string;
}

export interface ResetPasswordRequest {
  token: string;
  new_password: string;
}

export interface UserProfile {
  id: number;
  username: string;
  email: string;
  full_name?: string;
  first_name?: string;
  last_name?: string;
  role: string;
  is_active: boolean;
  organization_id?: number;
  organization?: {
    id: number;
    name: string;
    slug: string;
  };
}

export interface AuthUser extends UserProfile {
  // Campos adicionales para el usuario autenticado
  last_login?: string;
  created_at?: string;
  updated_at?: string;
}
