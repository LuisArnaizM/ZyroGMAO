/**
 * Servicio de mantenimiento
 */

import { apiClient } from '../utils/api-client';
import { buildUrl, buildQueryParams } from '../utils/helpers';
import {
  MaintenanceCreate,
  MaintenanceRead,
  MaintenanceUpdate,
  PaginationParams
} from '../types';

export interface MaintenanceFilters {
  search?: string;
  status?: string;
  maintenance_type?: string;
  asset_id?: number;
  user_id?: number;
  workorder_id?: number;
  date_from?: string;
  date_to?: string;
}

export class MaintenanceService {
  /**
   * Crear nuevo mantenimiento
   */
  async create(maintenanceData: MaintenanceCreate): Promise<MaintenanceRead> {
    return apiClient.post<MaintenanceRead>('/maintenance/', maintenanceData);
  }

  /**
   * Obtener lista de mantenimientos con paginación y filtros
   */
  async getAll(
    pagination?: PaginationParams,
    filters?: MaintenanceFilters
  ): Promise<MaintenanceRead[]> {
    const params = buildQueryParams(pagination, filters);
    const url = buildUrl('/maintenance/', params);
    return apiClient.get<MaintenanceRead[]>(url);
  }

  /**
   * Obtener mantenimiento por ID
   */
  async getById(maintenanceId: number): Promise<MaintenanceRead> {
    return apiClient.get<MaintenanceRead>(`/maintenance/${maintenanceId}`);
  }

  /**
   * Actualizar mantenimiento
   */
  async update(maintenanceId: number, maintenanceData: MaintenanceUpdate): Promise<MaintenanceRead> {
    return apiClient.put<MaintenanceRead>(`/maintenance/${maintenanceId}`, maintenanceData);
  }

  /**
   * Eliminar mantenimiento
   */
  async delete(maintenanceId: number): Promise<void> {
    await apiClient.delete(`/maintenance/${maintenanceId}`);
  }

  /**
   * Obtener mantenimientos por activo
   */
  async getByAsset(assetId: number): Promise<MaintenanceRead[]> {
    return apiClient.get<MaintenanceRead[]>(`/maintenance/asset/${assetId}`);
  }

  /**
   * Buscar mantenimientos por término
   */
  async search(
    searchTerm: string,
    pagination?: PaginationParams,
    filters?: Omit<MaintenanceFilters, 'search'>
  ): Promise<MaintenanceRead[]> {
    const params = buildQueryParams(pagination, { ...filters, search: searchTerm });
    const url = buildUrl('/maintenance/', params);
    return apiClient.get<MaintenanceRead[]>(url);
  }

  /**
   * Obtener mantenimientos por estado
   */
  async getByStatus(
    status: string,
    pagination?: PaginationParams
  ): Promise<MaintenanceRead[]> {
    const params = buildQueryParams(pagination, { status });
    const url = buildUrl('/maintenance/', params);
    return apiClient.get<MaintenanceRead[]>(url);
  }

  /**
   * Obtener mantenimientos por tipo
   */
  async getByType(
    maintenanceType: string,
    pagination?: PaginationParams
  ): Promise<MaintenanceRead[]> {
    const params = buildQueryParams(pagination, { maintenance_type: maintenanceType });
    const url = buildUrl('/maintenance/', params);
    return apiClient.get<MaintenanceRead[]>(url);
  }

  /**
   * Obtener mantenimientos por usuario
   */
  async getByUser(
    userId: number,
    pagination?: PaginationParams
  ): Promise<MaintenanceRead[]> {
    const params = buildQueryParams(pagination, { user_id: userId });
    const url = buildUrl('/maintenance/', params);
    return apiClient.get<MaintenanceRead[]>(url);
  }

  /**
   * Obtener mantenimientos por orden de trabajo
   */
  async getByWorkOrder(
    workorderId: number,
    pagination?: PaginationParams
  ): Promise<MaintenanceRead[]> {
    const params = buildQueryParams(pagination, { workorder_id: workorderId });
    const url = buildUrl('/maintenance/', params);
    return apiClient.get<MaintenanceRead[]>(url);
  }

  /**
   * Obtener mantenimientos programados
   */
  async getScheduled(pagination?: PaginationParams): Promise<MaintenanceRead[]> {
    return this.getByStatus('scheduled', pagination);
  }

  /**
   * Obtener mantenimientos en progreso
   */
  async getInProgress(pagination?: PaginationParams): Promise<MaintenanceRead[]> {
    return this.getByStatus('in_progress', pagination);
  }

  /**
   * Obtener mantenimientos completados
   */
  async getCompleted(pagination?: PaginationParams): Promise<MaintenanceRead[]> {
    return this.getByStatus('completed', pagination);
  }

  /**
   * Obtener mantenimientos preventivos
   */
  async getPreventive(pagination?: PaginationParams): Promise<MaintenanceRead[]> {
    return this.getByType('preventive', pagination);
  }

  /**
   * Obtener mantenimientos correctivos
   */
  async getCorrective(pagination?: PaginationParams): Promise<MaintenanceRead[]> {
    return this.getByType('corrective', pagination);
  }

  /**
   * Marcar mantenimiento como completado
   */
  async markAsCompleted(
    maintenanceId: number,
    completionData: {
      duration_hours?: number;
      cost?: number;
      notes?: string;
    }
  ): Promise<MaintenanceRead> {
    const updateData: MaintenanceUpdate = {
      status: 'completed',
      completed_date: new Date().toISOString(),
      ...completionData,
    };
    return this.update(maintenanceId, updateData);
  }

  /**
   * Iniciar mantenimiento
   */
  async start(maintenanceId: number): Promise<MaintenanceRead> {
    const updateData: MaintenanceUpdate = {
      status: 'in_progress',
    };
    return this.update(maintenanceId, updateData);
  }

  /**
   * Obtener mantenimientos vencidos
   */
  async getOverdue(pagination?: PaginationParams): Promise<MaintenanceRead[]> {
    const now = new Date().toISOString();
    const maintenances = await this.getScheduled(pagination);
    
    return maintenances.filter(maintenance => {
      if (!maintenance.scheduled_date) return false;
      return new Date(maintenance.scheduled_date) < new Date(now);
    });
  }

  /**
   * Obtener próximos mantenimientos
   */
  async getUpcoming(
    days: number = 7,
    pagination?: PaginationParams
  ): Promise<MaintenanceRead[]> {
    const now = new Date();
    const futureDate = new Date(now.getTime() + (days * 24 * 60 * 60 * 1000));
    
    const maintenances = await this.getScheduled(pagination);
    
    return maintenances.filter(maintenance => {
      if (!maintenance.scheduled_date) return false;
      const scheduledDate = new Date(maintenance.scheduled_date);
      return scheduledDate >= now && scheduledDate <= futureDate;
    });
  }

  /**
   * Obtener estadísticas de mantenimientos
   */
  async getStats(): Promise<{
    total: number;
    by_status: Record<string, number>;
    by_type: Record<string, number>;
    by_asset: Record<number, number>;
    scheduled: number;
    completed: number;
    overdue: number;
    avg_duration_hours?: number;
    total_cost: number;
  }> {
    const maintenances = await this.getAll({ page: 1, page_size: 1000 });
    
    const stats = {
      total: maintenances.length,
      by_status: {} as Record<string, number>,
      by_type: {} as Record<string, number>,
      by_asset: {} as Record<number, number>,
      scheduled: 0,
      completed: 0,
      overdue: 0,
      avg_duration_hours: undefined as number | undefined,
      total_cost: 0,
    };

    let totalDuration = 0;
    let durationCount = 0;
    const now = new Date();

    maintenances.forEach(maintenance => {
      // Contar por estado
      stats.by_status[maintenance.status] = (stats.by_status[maintenance.status] || 0) + 1;
      
      // Contar por tipo
      stats.by_type[maintenance.maintenance_type] = (stats.by_type[maintenance.maintenance_type] || 0) + 1;
      
      // Contar por activo
      stats.by_asset[maintenance.asset_id] = (stats.by_asset[maintenance.asset_id] || 0) + 1;
      
      // Contadores específicos
      if (maintenance.status === 'scheduled') {
        stats.scheduled++;
        
        // Verificar si está vencido
        if (maintenance.scheduled_date && new Date(maintenance.scheduled_date) < now) {
          stats.overdue++;
        }
      }
      
      if (maintenance.status === 'completed') {
        stats.completed++;
        
        // Sumar duración
        if (maintenance.duration_hours) {
          totalDuration += maintenance.duration_hours;
          durationCount++;
        }
      }
      
      // Sumar costo
      if (maintenance.cost) {
        stats.total_cost += maintenance.cost;
      }
    });

    // Calcular duración promedio
    if (durationCount > 0) {
      stats.avg_duration_hours = totalDuration / durationCount;
    }

    return stats;
  }

  /**
   * Obtener estadísticas de mantenimientos por activo
   */
  async getAssetMaintenanceStats(assetId: number): Promise<{
    total: number;
    by_status: Record<string, number>;
    by_type: Record<string, number>;
    scheduled: number;
    completed: number;
    last_maintenance_date?: string;
    next_maintenance_date?: string;
    avg_interval_days?: number;
  }> {
    const maintenances = await this.getByAsset(assetId);
    
    const stats = {
      total: maintenances.length,
      by_status: {} as Record<string, number>,
      by_type: {} as Record<string, number>,
      scheduled: 0,
      completed: 0,
      last_maintenance_date: undefined as string | undefined,
      next_maintenance_date: undefined as string | undefined,
      avg_interval_days: undefined as number | undefined,
    };

    const completedMaintenances = maintenances.filter(m => m.status === 'completed' && m.completed_date);
    const scheduledMaintenances = maintenances.filter(m => m.status === 'scheduled' && m.scheduled_date);

    maintenances.forEach(maintenance => {
      // Contar por estado
      stats.by_status[maintenance.status] = (stats.by_status[maintenance.status] || 0) + 1;
      
      // Contar por tipo
      stats.by_type[maintenance.maintenance_type] = (stats.by_type[maintenance.maintenance_type] || 0) + 1;
      
      // Contadores específicos
      if (maintenance.status === 'scheduled') stats.scheduled++;
      if (maintenance.status === 'completed') stats.completed++;
    });

    // Encontrar última fecha de mantenimiento
    if (completedMaintenances.length > 0) {
      const sortedCompleted = completedMaintenances.sort((a, b) => 
        new Date(b.completed_date!).getTime() - new Date(a.completed_date!).getTime()
      );
      stats.last_maintenance_date = sortedCompleted[0].completed_date!;
    }

    // Encontrar próxima fecha de mantenimiento
    if (scheduledMaintenances.length > 0) {
      const sortedScheduled = scheduledMaintenances.sort((a, b) => 
        new Date(a.scheduled_date!).getTime() - new Date(b.scheduled_date!).getTime()
      );
      stats.next_maintenance_date = sortedScheduled[0].scheduled_date!;
    }

    // Calcular intervalo promedio (simplificado)
    if (completedMaintenances.length >= 2) {
      const sortedDates = completedMaintenances
        .map(m => new Date(m.completed_date!))
        .sort((a, b) => a.getTime() - b.getTime());
      
      let totalInterval = 0;
      for (let i = 1; i < sortedDates.length; i++) {
        const interval = sortedDates[i].getTime() - sortedDates[i - 1].getTime();
        totalInterval += interval / (1000 * 60 * 60 * 24); // convertir a días
      }
      
      stats.avg_interval_days = totalInterval / (sortedDates.length - 1);
    }

    return stats;
  }

  /**
   * Programar mantenimiento preventivo
   */
  async schedulePreventive(
    assetId: number,
    userId: number,
    scheduledDate: string,
    description: string
  ): Promise<MaintenanceRead> {
    const maintenanceData: MaintenanceCreate = {
      description,
      asset_id: assetId,
      user_id: userId,
      maintenance_type: 'preventive',
      scheduled_date: scheduledDate,
    };
    
    return this.create(maintenanceData);
  }
}

// Instancia global del servicio
export const maintenanceService = new MaintenanceService();
