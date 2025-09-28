/**
 * Servicio de sensores
 */

import { apiClient } from '../utils/api-client';
import { buildUrl, buildQueryParams } from '../utils/helpers';
import {
  SensorConfigCreate,
  SensorConfigRead,
  SensorConfigUpdate,
  PaginationParams,
  FilterParams
} from '../types';

export interface SensorFilters extends FilterParams {
  sensor_type?: string;
  is_active?: boolean;
  asset_id?: number;
}

export class SensorService {
  /**
   * Crear nueva configuración de sensor
   */
  async create(sensorData: SensorConfigCreate): Promise<SensorConfigRead> {
    return apiClient.post<SensorConfigRead>('/sensors/', sensorData);
  }

  /**
   * Obtener lista de sensores con paginación y filtros
   */
  async getAll(
    pagination?: PaginationParams,
    filters?: SensorFilters
  ): Promise<SensorConfigRead[]> {
    const params = buildQueryParams(pagination, filters);
    const url = buildUrl('/sensors/', params);
    return apiClient.get<SensorConfigRead[]>(url);
  }

  /**
   * Obtener sensor por ID
   */
  async getById(sensorId: number): Promise<SensorConfigRead> {
    return apiClient.get<SensorConfigRead>(`/sensors/${sensorId}`);
  }

  /**
   * Actualizar configuración de sensor
   */
  async update(sensorId: number, sensorData: SensorConfigUpdate): Promise<SensorConfigRead> {
    return apiClient.put<SensorConfigRead>(`/sensors/${sensorId}`, sensorData);
  }

  /**
   * Eliminar configuración de sensor
   */
  async delete(sensorId: number): Promise<void> {
    await apiClient.delete(`/sensors/${sensorId}`);
  }

  /**
   * Obtener sensores por activo
   */
  async getByAsset(assetId: number): Promise<SensorConfigRead[]> {
    return apiClient.get<SensorConfigRead[]>(`/sensors/asset/${assetId}`);
  }

  /**
   * Buscar sensores por término
   */
  async search(
    searchTerm: string,
    pagination?: PaginationParams,
    filters?: SensorFilters
  ): Promise<SensorConfigRead[]> {
    const params = buildQueryParams(pagination, { ...filters, search: searchTerm });
    const url = buildUrl('/sensors/', params);
    return apiClient.get<SensorConfigRead[]>(url);
  }

  /**
   * Obtener sensores por tipo
   */
  async getByType(
    sensorType: string,
    pagination?: PaginationParams
  ): Promise<SensorConfigRead[]> {
    const params = buildQueryParams(pagination, { sensor_type: sensorType });
    const url = buildUrl('/sensors/', params);
    return apiClient.get<SensorConfigRead[]>(url);
  }

  /**
   * Obtener sensores activos/inactivos
   */
  async getByStatus(
    isActive: boolean,
    pagination?: PaginationParams
  ): Promise<SensorConfigRead[]> {
    const params = buildQueryParams(pagination, { is_active: isActive });
    const url = buildUrl('/sensors/', params);
    return apiClient.get<SensorConfigRead[]>(url);
  }

  /**
   * Obtener tipos de sensores disponibles
   */
  async getSensorTypes(): Promise<string[]> {
    // Esta funcionalidad requeriría un endpoint específico en el backend
    // Por ahora, obtenemos todos los sensores y extraemos los tipos únicos
    const sensors = await this.getAll({ page: 1, page_size: 1000 });
    const types = [...new Set(sensors.map(sensor => sensor.sensor_type))];
    return types.sort();
  }

  /**
   * Obtener sensores por rango de valores
   */
  async getByValueRange(
    minValue?: number,
    maxValue?: number,
    pagination?: PaginationParams
  ): Promise<SensorConfigRead[]> {
    // Como la API no tiene filtros específicos para rangos, obtenemos todos y filtramos
    const sensors = await this.getAll(pagination);
    
    return sensors.filter(sensor => {
      if (minValue !== undefined && sensor.min_value !== null && sensor.min_value !== undefined && sensor.min_value < minValue) {
        return false;
      }
      if (maxValue !== undefined && sensor.max_value !== null && sensor.max_value !== undefined && sensor.max_value > maxValue) {
        return false;
      }
      return true;
    });
  }

  /**
   * Obtener estadísticas de sensores
   */
  async getStats(): Promise<{
    total: number;
    by_type: Record<string, number>;
    by_asset: Record<number, number>;
    active: number;
    inactive: number;
  }> {
    const sensors = await this.getAll({ page: 1, page_size: 1000 });
    
    const stats = {
      total: sensors.length,
      by_type: {} as Record<string, number>,
      by_asset: {} as Record<number, number>,
      active: 0,
      inactive: 0,
    };

    sensors.forEach(sensor => {
      // Contar por tipo
      stats.by_type[sensor.sensor_type] = (stats.by_type[sensor.sensor_type] || 0) + 1;
      
      // Contar por activo
      stats.by_asset[sensor.asset_id] = (stats.by_asset[sensor.asset_id] || 0) + 1;
      
      // Contar activos/inactivos (asumiendo que todos están activos por defecto)
      stats.active++;
    });

    return stats;
  }

  /**
   * Obtener estadísticas de sensores por activo
   */
  async getAssetSensorStats(assetId: number): Promise<{
    total: number;
    by_type: Record<string, number>;
    with_limits: number;
    without_limits: number;
  }> {
    const sensors = await this.getByAsset(assetId);
    
    const stats = {
      total: sensors.length,
      by_type: {} as Record<string, number>,
      with_limits: 0,
      without_limits: 0,
    };

    sensors.forEach(sensor => {
      // Contar por tipo
      stats.by_type[sensor.sensor_type] = (stats.by_type[sensor.sensor_type] || 0) + 1;
      
      // Contar sensores con/sin límites
      if (sensor.min_value !== null || sensor.max_value !== null) {
        stats.with_limits++;
      } else {
        stats.without_limits++;
      }
    });

    return stats;
  }

  /**
   * Validar configuración de sensor
   */
  validateSensorConfig(sensorData: SensorConfigCreate | SensorConfigUpdate): {
    isValid: boolean;
    errors: string[];
  } {
    const errors: string[] = [];

    // Validar que min_value sea menor que max_value
    if (
      sensorData.min_value !== undefined && 
      sensorData.max_value !== undefined &&
      sensorData.min_value !== null && 
      sensorData.max_value !== null &&
      sensorData.min_value >= sensorData.max_value
    ) {
      errors.push('El valor mínimo debe ser menor que el valor máximo');
    }

    return {
      isValid: errors.length === 0,
      errors,
    };
  }
}

// Instancia global del servicio
export const sensorService = new SensorService();
