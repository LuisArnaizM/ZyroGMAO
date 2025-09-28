/**
 * Servicio de fallos
 */

import { apiClient } from '../utils/api-client';
import { buildUrl, buildQueryParams } from '../utils/helpers';
import {
  FailureCreate,
  FailureRead,
  FailureUpdate,
  FailureWithWorkOrder,
  PaginationParams,
  Severity
} from '../types';

export interface FailureFilters {
  search?: string;
  status?: string;
  severity?: Severity;
  asset_id?: number;
  reported_by?: number;
  date_from?: string;
  date_to?: string;
}

export class FailureService {
  /**
   * Crear nuevo fallo
   */
  async create(failureData: FailureCreate): Promise<FailureRead> {
    return apiClient.post<FailureRead>('/failures/', failureData);
  }

  /**
   * Obtener lista de fallos con paginación y filtros
   */
  async getAll(
    pagination?: PaginationParams,
    filters?: FailureFilters
  ): Promise<FailureRead[]> {
    const params = buildQueryParams(pagination, filters);
    const url = buildUrl('/failures/', params);
    return apiClient.get<FailureRead[]>(url);
  }

  /**
   * Obtener lista de fallos con sus workorder_ids asociados
   */
  async getFailuresWithWorkOrders(): Promise<FailureWithWorkOrder[]> {
    return apiClient.get<FailureWithWorkOrder[]>('/failures/with-workorders');
  }

  /**
   * Obtener fallo por ID
   */
  async getById(failureId: number): Promise<FailureRead> {
    return apiClient.get<FailureRead>(`/failures/${failureId}`);
  }

  /**
   * Actualizar fallo
   */
  async update(failureId: number, failureData: FailureUpdate): Promise<FailureRead> {
    return apiClient.put<FailureRead>(`/failures/${failureId}`, failureData);
  }

  /**
   * Eliminar fallo
   */
  async delete(failureId: number): Promise<void> {
    await apiClient.delete(`/failures/${failureId}`);
  }

  /**
   * Obtener fallos por activo
   */
  async getByAsset(assetId: number): Promise<FailureRead[]> {
    return apiClient.get<FailureRead[]>(`/failures/asset/${assetId}`);
  }

  /**
   * Buscar fallos por término
   */
  async search(
    searchTerm: string,
    pagination?: PaginationParams,
    filters?: Omit<FailureFilters, 'search'>
  ): Promise<FailureRead[]> {
    const params = buildQueryParams(pagination, { ...filters, search: searchTerm });
    const url = buildUrl('/failures/', params);
    return apiClient.get<FailureRead[]>(url);
  }

  /**
   * Obtener fallos por estado
   */
  async getByStatus(
    status: string,
    pagination?: PaginationParams
  ): Promise<FailureRead[]> {
    const params = buildQueryParams(pagination, { status });
    const url = buildUrl('/failures/', params);
    return apiClient.get<FailureRead[]>(url);
  }

  /**
   * Obtener fallos por severidad
   */
  async getBySeverity(
    severity: Severity,
    pagination?: PaginationParams
  ): Promise<FailureRead[]> {
    const params = buildQueryParams(pagination, { severity });
    const url = buildUrl('/failures/', params);
    return apiClient.get<FailureRead[]>(url);
  }

  /**
   * Obtener fallos pendientes
   */
  async getPending(pagination?: PaginationParams): Promise<FailureRead[]> {
    return this.getByStatus('pending', pagination);
  }

  /**
   * Obtener fallos críticos
   */
  async getCritical(pagination?: PaginationParams): Promise<FailureRead[]> {
    return this.getBySeverity('critical', pagination);
  }

  /**
   * Obtener fallos por usuario que reportó
   */
  async getByReporter(
    reporterId: number,
    pagination?: PaginationParams
  ): Promise<FailureRead[]> {
    const params = buildQueryParams(pagination, { reported_by: reporterId });
    const url = buildUrl('/failures/', params);
    return apiClient.get<FailureRead[]>(url);
  }

  /**
   * Obtener fallos por rango de fechas
   */
  async getByDateRange(
    dateFrom: string,
    dateTo: string,
    pagination?: PaginationParams
  ): Promise<FailureRead[]> {
    const params = buildQueryParams(pagination, { date_from: dateFrom, date_to: dateTo });
    const url = buildUrl('/failures/', params);
    return apiClient.get<FailureRead[]>(url);
  }

  /**
   * Marcar fallo como resuelto
   */
  async markAsResolved(
    failureId: number,
    resolutionNotes?: string
  ): Promise<FailureRead> {
    const updateData: FailureUpdate = {
      status: 'resolved',
      resolved_date: new Date().toISOString(),
      resolution_notes: resolutionNotes,
    };
    return this.update(failureId, updateData);
  }

  /**
   * Obtener estadísticas de fallos
   */
  async getStats(): Promise<{
    total: number;
    by_status: Record<string, number>;
    by_severity: Record<string, number>;
    by_asset: Record<number, number>;
    pending: number;
    resolved: number;
    critical: number;
  }> {
    const failures = await this.getAll({ page: 1, page_size: 1000 });
    
    const stats = {
      total: failures.length,
      by_status: {} as Record<string, number>,
      by_severity: {} as Record<string, number>,
      by_asset: {} as Record<number, number>,
      pending: 0,
      resolved: 0,
      critical: 0,
    };

    failures.forEach(failure => {
      // Contar por estado
      stats.by_status[failure.status] = (stats.by_status[failure.status] || 0) + 1;
      
      // Contar por severidad
      stats.by_severity[failure.severity] = (stats.by_severity[failure.severity] || 0) + 1;
      
      // Contar por activo
      if (failure.asset_id !== undefined) {
        stats.by_asset[failure.asset_id] = (stats.by_asset[failure.asset_id] || 0) + 1;
      }
      
      // Contadores específicos
      if (failure.status === 'pending') stats.pending++;
      if (failure.status === 'resolved') stats.resolved++;
      if (failure.severity === 'critical') stats.critical++;
    });

    return stats;
  }

  /**
   * Obtener estadísticas de fallos por activo
   */
  async getAssetFailureStats(assetId: number): Promise<{
    total: number;
    by_status: Record<string, number>;
    by_severity: Record<string, number>;
    pending: number;
    resolved: number;
    avg_resolution_time_hours?: number;
  }> {
    const failures = await this.getByAsset(assetId);
    
    const stats = {
      total: failures.length,
      by_status: {} as Record<string, number>,
      by_severity: {} as Record<string, number>,
      pending: 0,
      resolved: 0,
      avg_resolution_time_hours: undefined as number | undefined,
    };

    let totalResolutionTime = 0;
    let resolvedCount = 0;

    failures.forEach(failure => {
      // Contar por estado
      stats.by_status[failure.status] = (stats.by_status[failure.status] || 0) + 1;
      
      // Contar por severidad
      stats.by_severity[failure.severity] = (stats.by_severity[failure.severity] || 0) + 1;
      
      // Contadores específicos
      if (failure.status === 'pending') stats.pending++;
      if (failure.status === 'resolved') {
        stats.resolved++;
        
        // Calcular tiempo de resolución
        if (failure.resolved_date) {
          const reportedDate = new Date(failure.reported_date);
          const resolvedDate = new Date(failure.resolved_date);
          const resolutionTimeMs = resolvedDate.getTime() - reportedDate.getTime();
          const resolutionTimeHours = resolutionTimeMs / (1000 * 60 * 60);
          
          totalResolutionTime += resolutionTimeHours;
          resolvedCount++;
        }
      }
    });

    // Calcular tiempo promedio de resolución
    if (resolvedCount > 0) {
      stats.avg_resolution_time_hours = totalResolutionTime / resolvedCount;
    }

    return stats;
  }

  /**
   * Exportar fallos a CSV
   */
  async exportToCSV(filters?: FailureFilters): Promise<string> {
    const failures = await this.getAll({ page: 1, page_size: 10000 }, filters);
    
    const headers = [
      'ID',
      'Descripción',
      'Estado',
      'Severidad',
      'Activo ID',
      'Reportado por',
      'Fecha de reporte',
      'Fecha de resolución',
      'Notas de resolución'
    ];
    
    const csvContent = [
      headers.join(','),
      ...failures.map(failure => [
        failure.id,
        `"${failure.description.replace(/"/g, '""')}"`,
        failure.status,
        failure.severity,
        failure.asset_id,
        failure.reported_by,
        failure.reported_date,
        failure.resolved_date || '',
        failure.resolution_notes ? `"${failure.resolution_notes.replace(/"/g, '""')}"` : ''
      ].join(','))
    ].join('\n');
    
    return csvContent;
  }
}

// Instancia global del servicio
export const failureService = new FailureService();
