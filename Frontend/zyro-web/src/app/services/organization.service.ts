/**
 * Servicio de organizaciones
 */

import { apiClient } from '../utils/api-client';
import { buildUrl, buildQueryParams } from '../utils/helpers';
import {
  OrganizationCreate,
  OrganizationRead,
  OrganizationUpdate,
  OrganizationStats,
  PaginationParams
} from '../types';

export interface OrganizationFilters {
  search?: string;
  active_only?: boolean;
}

export class OrganizationService {
  /**
   * Crear nueva organización (solo super admin)
   */
  async create(orgData: OrganizationCreate): Promise<OrganizationRead> {
    return apiClient.post<OrganizationRead>('/organization/', orgData);
  }

  /**
   * Listar organizaciones (solo super admin)
   */
  async getAll(
    pagination?: PaginationParams,
    filters?: OrganizationFilters
  ): Promise<{ 
    organizations: OrganizationRead[]; 
    total: number; 
    page: number; 
    page_size: number; 
  }> {
    const params = buildQueryParams(pagination, filters);
    const url = buildUrl('/organization/', params);
    return apiClient.get(url);
  }

  /**
   * Obtener organización actual del usuario
   */
  async getCurrent(): Promise<OrganizationRead> {
    return apiClient.get<OrganizationRead>('/organization/current');
  }

  /**
   * Actualizar organización actual (org admin)
   */
  async updateCurrent(orgData: OrganizationUpdate): Promise<OrganizationRead> {
    return apiClient.put<OrganizationRead>('/organization/current', orgData);
  }

  /**
   * Obtener estadísticas de la organización actual
   */
  async getCurrentStats(): Promise<OrganizationStats> {
    return apiClient.get<OrganizationStats>('/organization/current/stats');
  }

  /**
   * Obtener organización por slug (solo super admin)
   */
  async getBySlug(slug: string): Promise<OrganizationRead> {
    return apiClient.get<OrganizationRead>(`/organization/slug/${slug}`);
  }

  /**
   * Obtener organización por ID (solo super admin)
   */
  async getById(orgId: number): Promise<OrganizationRead> {
    return apiClient.get<OrganizationRead>(`/organization/${orgId}`);
  }

  /**
   * Actualizar organización (solo super admin)
   */
  async update(orgId: number, orgData: OrganizationUpdate): Promise<OrganizationRead> {
    return apiClient.put<OrganizationRead>(`/organization/${orgId}`, orgData);
  }

  /**
   * Eliminar (desactivar) organización (solo super admin)
   */
  async delete(orgId: number): Promise<void> {
    await apiClient.delete(`/organization/${orgId}`);
  }

  /**
   * Obtener estadísticas de una organización (solo super admin)
   */
  async getStats(orgId: number): Promise<OrganizationStats> {
    return apiClient.get<OrganizationStats>(`/organization/${orgId}/stats`);
  }

  /**
   * Buscar organizaciones
   */
  async search(
    searchTerm: string,
    pagination?: PaginationParams,
    activeOnly: boolean = true
  ): Promise<{ 
    organizations: OrganizationRead[]; 
    total: number; 
    page: number; 
    page_size: number; 
  }> {
    const params = buildQueryParams(pagination, { 
      search: searchTerm, 
      active_only: activeOnly 
    });
    const url = buildUrl('/organization/', params);
    return apiClient.get(url);
  }

  /**
   * Validar disponibilidad de slug
   */
  async validateSlug(slug: string): Promise<boolean> {
    try {
      await this.getBySlug(slug);
      return false; // Si encuentra la organización, el slug no está disponible
    } catch (error) {
      console.log(error);
      return true; // Si no encuentra la organización, el slug está disponible
    }
  }
}

// Instancia global del servicio
export const organizationService = new OrganizationService();
