/**
 * Tipos para sensores
 */

export interface SensorConfigCreate {
  asset_id: number;
  name: string;
  sensor_type: string;
  location?: string;
  units?: string;
  min_value?: number;
  max_value?: number;
}

export interface SensorConfigRead {
  id: number;
  asset_id: number;
  name: string;
  sensor_type: string;
  location?: string;
  units?: string;
  min_value?: number;
  max_value?: number;
  created_at: string;
  updated_at?: string;
}

export interface SensorConfigUpdate {
  name?: string;
  sensor_type?: string;
  location?: string;
  units?: string;
  min_value?: number;
  max_value?: number;
}
