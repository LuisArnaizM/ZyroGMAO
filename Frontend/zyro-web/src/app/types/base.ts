/**
 * Tipos base para la API de Gestión de Mantenimiento Industrial
 */

// Tipos de respuesta común
export interface ApiResponse<T = unknown> {
  data?: T;
  message?: string;
  success: boolean;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

// Parámetros de paginación
export interface PaginationParams {
  page?: number;
  page_size?: number;
  search?: string;
}

// Tipos de filtros comunes
export interface FilterParams {
  search?: string;
  status?: string;
  priority?: string;
  severity?: string;
  // Filtros específicos de asset
  asset_type?: string;
  location?: string;
  responsible_id?: number;
  warranty_expiring?: boolean;
  // Filtros específicos de failure
  reported_by?: number;
  date_from?: string;
  date_to?: string;
  // Filtros específicos de maintenance
  maintenance_type?: string;
  user_id?: number;
  workorder_id?: number;
  // Filtros específicos de organization
  active_only?: boolean;
  // Filtros específicos de sensor
  sensor_type?: string;
  is_active?: boolean;
  // Filtros específicos de user
  role?: string;
}

// Errores de validación
export interface ValidationError {
  loc: (string | number)[];
  msg: string;
  type: string;
}

export interface HTTPValidationError {
  detail: ValidationError[];
}

// Configuración de autenticación
export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
}

export interface RefreshTokenRequest {
  refresh_token: string;
}

// Tipos de estado comunes
export type Status = 'pending' | 'in_progress' | 'completed' | 'cancelled' | 'failed';
export type Priority = 'low' | 'medium' | 'high' | 'urgent';
export type Severity = 'low' | 'medium' | 'high' | 'critical';
export type Role = 'Admin' | 'Supervisor' | 'Tecnico' | 'Consultor';
