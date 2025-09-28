
import { ApiClient, apiClient } from '../utils/api-client';
import { buildUrl, buildQueryParams } from '../utils/helpers';
import {
  UserCreate,
  UserRead,
  UserUpdate,
  PaginationParams,
  FilterParams
} from '../types';

export interface UserFilters extends FilterParams {
  role?: string;
  is_active?: boolean;
  organization_id?: number;
}

export class UserService {
  private apiClient: ApiClient;

  constructor(client?: ApiClient) {
    this.apiClient = client || apiClient;
  }

  /**
   * Obtener usuarios que son managers de departamento
   */
  async getManagers(): Promise<UserRead[]> {
    return this.apiClient.get<UserRead[]>('/users/managers');
  }

  /**
   * Crear nuevo usuario
   */
  async create(userData: UserCreate): Promise<UserRead> {
    return this.apiClient.post<UserRead>('/users/', userData);
  }

  /**
   * Obtener lista de usuarios con paginación y filtros
   */
  async getAll(
    pagination?: PaginationParams,
    filters?: UserFilters
  ): Promise<UserRead[]> {
    const params = buildQueryParams(pagination, filters);
    const url = buildUrl('/users/', params);
    return this.apiClient.get<UserRead[]>(url);
  }

  /**
   * Obtener usuario por ID
   */
  async getById(userId: number): Promise<UserRead> {
    return this.apiClient.get<UserRead>(`/users/${userId}`);
  }

  /**
   * Obtener perfil del usuario actual
   */
  async getMe(): Promise<UserRead> {
    return this.apiClient.get<UserRead>('/users/me');
  }

  /**
   * Actualizar usuario
   */
  async update(userId: number, userData: UserUpdate): Promise<UserRead> {
    return this.apiClient.put<UserRead>(`/users/${userId}`, userData);
  }

  /**
   * Eliminar usuario
   */
  async delete(userId: number): Promise<void> {
    await this.apiClient.delete(`/users/${userId}`);
  }

  /**
   * Cambiar contraseña de un usuario (admin)
   */
  async changeUserPassword(userId: number, password: string): Promise<void> {
    await this.apiClient.put(`/users/${userId}/password`, { password });
  }

  /**
   * Buscar usuarios por término
   */
  async search(
    searchTerm: string,
    pagination?: PaginationParams,
    filters?: UserFilters
  ): Promise<UserRead[]> {
    const params = buildQueryParams(pagination, { ...filters, search: searchTerm });
    const url = buildUrl('/users/', params);
    return this.apiClient.get<UserRead[]>(url);
  }

  /**
   * Obtener usuarios por rol
   */
  async getByRole(
    role: string,
    pagination?: PaginationParams
  ): Promise<UserRead[]> {
    const params = buildQueryParams(pagination, { role });
    const url = buildUrl('/users/', params);
    return this.apiClient.get<UserRead[]>(url);
  }

  /**
   * Obtener usuarios activos/inactivos
   */
  async getByStatus(
    isActive: boolean,
    pagination?: PaginationParams
  ): Promise<UserRead[]> {
    const params = buildQueryParams(pagination, { is_active: isActive });
    const url = buildUrl('/users/', params);
    return this.apiClient.get<UserRead[]>(url);
  }
}

// Export the class and a global instance
export const userService = new UserService();

// Export the class only, no global instance
// Each component should create its own instance with the appropriate ApiClient
