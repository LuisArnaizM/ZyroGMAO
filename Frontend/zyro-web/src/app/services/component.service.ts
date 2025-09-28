/**
 * Servicio de componentes
 */

import { apiClient } from '../utils/api-client';
import { buildUrl } from '../utils/helpers';
import {
  ComponentCreate,
  ComponentRead,
  ComponentUpdate,
  ComponentDetail,
} from '../types';

export interface ComponentFilters {
  asset_id?: number;
  component_type?: string;
  status?: string;
  responsible_id?: number;
  needs_maintenance?: boolean;
}

export class ComponentService {
  /**
   * Crear nuevo componente
   */
  async create(componentData: ComponentCreate): Promise<ComponentRead> {
    return apiClient.post<ComponentRead>('/components/', componentData);
  }

  /**
   * Obtener lista de componentes con filtros
   */
  async getAll(filters?: ComponentFilters): Promise<ComponentRead[]> {
    const params = {
      asset_id: filters?.asset_id,
      skip: 0,
      limit: 100,
    };
    const url = buildUrl('/components/', params);
    return apiClient.get<ComponentRead[]>(url);
  }

  /**
   * Obtener componente por ID con detalles
   */
  async getById(componentId: number): Promise<ComponentDetail> {
    return apiClient.get<ComponentDetail>(`/components/${componentId}`);
  }

  /**
   * Actualizar componente
   */
  async update(componentId: number, componentData: ComponentUpdate): Promise<ComponentRead> {
    return apiClient.put<ComponentRead>(`/components/${componentId}`, componentData);
  }

  /**
   * Eliminar componente
   */
  async delete(componentId: number): Promise<void> {
    await apiClient.delete(`/components/${componentId}`);
  }

  /**
   * Obtener componentes por activo
   */
  async getByAsset(assetId: number): Promise<ComponentRead[]> {
    return apiClient.get<ComponentRead[]>(`/components/asset/${assetId}`);
  }

  /**
   * Obtener estadísticas de un componente
   */
  async getStatistics(componentId: number): Promise<Record<string, unknown>> {
    return apiClient.get(`/components/${componentId}/statistics`);
  }

  /**
   * Obtener componentes con paginación
   */
  async getPaginated(
    skip: number = 0,
    limit: number = 100,
    filters?: ComponentFilters
  ): Promise<ComponentRead[]> {
    const params = {
      skip,
      limit,
      ...filters,
    };
    const url = buildUrl('/components/', params);
    return apiClient.get<ComponentRead[]>(url);
  }

  /**
   * Obtener componentes por tipo
   */
  async getByType(
    componentType: string,
    assetId?: number
  ): Promise<ComponentRead[]> {
    const filters: ComponentFilters = { component_type: componentType };
    if (assetId) {
      filters.asset_id = assetId;
    }
    return this.getAll(filters);
  }

  /**
   * Obtener componentes por estado
   */
  async getByStatus(
    status: string,
    assetId?: number
  ): Promise<ComponentRead[]> {
    const filters: ComponentFilters = { status };
    if (assetId) {
      filters.asset_id = assetId;
    }
    return this.getAll(filters);
  }

  /**
   * Obtener componentes que necesitan mantenimiento
   */
  async getNeedingMaintenance(assetId?: number): Promise<ComponentDetail[]> {
    // Esta funcionalidad requiere obtener los detalles de cada componente
    const components = await this.getAll(assetId ? { asset_id: assetId } : undefined);
    
    const detailedComponents = await Promise.all(
      components.map(component => this.getById(component.id))
    );
    
    return detailedComponents.filter(component => component.needs_maintenance);
  }

  /**
   * Obtener componentes por responsable
   */
  async getByResponsible(
    responsibleId: number,
    assetId?: number
  ): Promise<ComponentRead[]> {
    const filters: ComponentFilters = { responsible_id: responsibleId };
    if (assetId) {
      filters.asset_id = assetId;
    }
    return this.getAll(filters);
  }

  /**
   * Buscar componentes
   */
  async search(
    searchTerm: string,
    assetId?: number
  ): Promise<ComponentRead[]> {
    // Como la API no tiene búsqueda directa, obtenemos todos y filtramos
    const components = await this.getAll(assetId ? { asset_id: assetId } : undefined);
    
    const lowerSearchTerm = searchTerm.toLowerCase();
    return components.filter(component =>
      component.name.toLowerCase().includes(lowerSearchTerm) ||
      component.component_type.toLowerCase().includes(lowerSearchTerm) ||
      (component.description && component.description.toLowerCase().includes(lowerSearchTerm)) ||
      (component.model && component.model.toLowerCase().includes(lowerSearchTerm)) ||
      (component.serial_number && component.serial_number.toLowerCase().includes(lowerSearchTerm))
    );
  }

  /**
   * Obtener estadísticas de componentes por activo
   */
  async getAssetComponentStats(assetId: number): Promise<{
    total: number;
    by_status: Record<string, number>;
    by_type: Record<string, number>;
    needing_maintenance: number;
  }> {
    const components = await this.getByAsset(assetId);
    
    const stats = {
      total: components.length,
      by_status: {} as Record<string, number>,
      by_type: {} as Record<string, number>,
      needing_maintenance: 0,
    };

    // Obtener detalles para verificar mantenimiento
    const detailedComponents = await Promise.all(
      components.map(component => this.getById(component.id))
    );

    detailedComponents.forEach(component => {
      // Contar por estado
      stats.by_status[component.status] = (stats.by_status[component.status] || 0) + 1;
      
      // Contar por tipo
      stats.by_type[component.component_type] = (stats.by_type[component.component_type] || 0) + 1;
      
      // Contar los que necesitan mantenimiento
      if (component.needs_maintenance) {
        stats.needing_maintenance++;
      }
    });

    return stats;
  }
}

// Instancia global del servicio
export const componentService = new ComponentService();
