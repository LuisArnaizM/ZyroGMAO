/**
 * Servicio de activos
 */

import { ApiClient, apiClient } from '../utils/api-client';
import { buildUrl, buildQueryParams } from '../utils/helpers';
import {
  AssetCreate,
  AssetRead,
  AssetUpdate,
  PaginationParams,
  FilterParams
} from '../types';

export interface AssetFilters extends FilterParams {
  asset_type?: string;
  location?: string;
  responsible_id?: number;
  warranty_expiring?: boolean; // Assets with warranty expiring soon
}

export class AssetService {
  private apiClient: ApiClient;

  constructor(client?: ApiClient) {
    this.apiClient = client || apiClient;
  }

  /**
   * Set authentication token for the service
   */
  setAuthToken(token: string, refreshToken?: string): void {
    this.apiClient.setTokens(token, refreshToken);
  }

  /**
   * Crear nuevo activo
   */
  async create(assetData: AssetCreate): Promise<AssetRead> {
    return this.apiClient.post<AssetRead>('/assets/', assetData);
  }

  /**
   * Obtener lista de activos con paginación y filtros
   */
  async getAll(
    pagination?: PaginationParams,
    filters?: AssetFilters
  ): Promise<AssetRead[]> {
    const params = buildQueryParams(pagination, filters);
    const url = buildUrl('/assets/', params);
    return this.apiClient.get<AssetRead[]>(url);
  }

  /**
   * Obtener activo por ID
   */
  async getById(assetId: number): Promise<AssetRead> {
    return this.apiClient.get<AssetRead>(`/assets/${assetId}`);
  }

  /**
   * Actualizar activo
   */
  async update(assetId: number, assetData: AssetUpdate): Promise<AssetRead> {
    return this.apiClient.put<AssetRead>(`/assets/${assetId}`, assetData);
  }

  /**
   * Eliminar activo
   */
  async delete(assetId: number): Promise<void> {
    await this.apiClient.delete(`/assets/${assetId}`);
  }

  /**
   * Buscar activos por término
   */
  async search(
    searchTerm: string,
    pagination?: PaginationParams,
    filters?: AssetFilters
  ): Promise<AssetRead[]> {
    const params = buildQueryParams(pagination, { ...filters, search: searchTerm });
    const url = buildUrl('/assets/', params);
    return this.apiClient.get<AssetRead[]>(url);
  }

  /**
   * Obtener activos por tipo
   */
  async getByType(
    assetType: string,
    pagination?: PaginationParams
  ): Promise<AssetRead[]> {
    const params = buildQueryParams(pagination, { asset_type: assetType });
    const url = buildUrl('/assets/', params);
    return this.apiClient.get<AssetRead[]>(url);
  }

  /**
   * Obtener activos por estado
   */
  async getByStatus(
    status: string,
    pagination?: PaginationParams
  ): Promise<AssetRead[]> {
    const params = buildQueryParams(pagination, { status });
    const url = buildUrl('/assets/', params);
    return this.apiClient.get<AssetRead[]>(url);
  }

  /**
   * Obtener activos por ubicación
   */
  async getByLocation(
    location: string,
    pagination?: PaginationParams
  ): Promise<AssetRead[]> {
    const params = buildQueryParams(pagination, { location });
    const url = buildUrl('/assets/', params);
    return this.apiClient.get<AssetRead[]>(url);
  }

  /**
   * Obtener activos por responsable
   */
  async getByResponsible(
    responsibleId: number,
    pagination?: PaginationParams
  ): Promise<AssetRead[]> {
    const params = buildQueryParams(pagination, { responsible_id: responsibleId });
    const url = buildUrl('/assets/', params);
    return this.apiClient.get<AssetRead[]>(url);
  }

  /**
   * Obtener activos con garantía próxima a vencer
   */
  async getWithExpiringWarranty(
    pagination?: PaginationParams
  ): Promise<AssetRead[]> {
    // Implementar lógica en el frontend para filtrar por fecha de garantía
    const allAssets = await this.getAll(pagination);
    const now = new Date();
    const threeMonthsFromNow = new Date(now.getTime() + (90 * 24 * 60 * 60 * 1000));
    
    return allAssets.filter(asset => {
      if (!asset.warranty_expiry) return false;
      const warrantyDate = new Date(asset.warranty_expiry);
      return warrantyDate <= threeMonthsFromNow && warrantyDate > now;
    });
  }

  /**
   * Obtener estadísticas de activos
   */
  async getStats(): Promise<{
    total: number;
    by_status: Record<string, number>;
    by_type: Record<string, number>;
    warranty_expiring: number;
  }> {
    // Esta funcionalidad requeriría un endpoint específico en el backend
    // Por ahora, calculamos las estadísticas en el frontend
    const assets = await this.getAll({ page: 1, page_size: 1000 });
    
    const stats = {
      total: assets.length,
      by_status: {} as Record<string, number>,
      by_type: {} as Record<string, number>,
      warranty_expiring: 0,
    };

    assets.forEach(asset => {
      // Contar por estado
      stats.by_status[asset.status] = (stats.by_status[asset.status] || 0) + 1;
      
      // Contar por tipo
      stats.by_type[asset.asset_type] = (stats.by_type[asset.asset_type] || 0) + 1;
      
      // Contar garantías próximas a vencer
      if (asset.warranty_expiry) {
        const warrantyDate = new Date(asset.warranty_expiry);
        const now = new Date();
        const threeMonthsFromNow = new Date(now.getTime() + (90 * 24 * 60 * 60 * 1000));
        
        if (warrantyDate <= threeMonthsFromNow && warrantyDate > now) {
          stats.warranty_expiring++;
        }
      }
    });

    return stats;
  }
}

// Export the class and a global instance
export const assetService = new AssetService();
