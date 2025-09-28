/**
 * Tipos para mantenimiento
 */

export interface MaintenanceCreate {
  description: string;
  asset_id: number;
  user_id: number;
  maintenance_type?: string;
  scheduled_date?: string;
  workorder_id?: number;
}

export interface MaintenanceRead {
  id: number;
  description: string;
  status: string;
  maintenance_type: string;
  asset_id: number;
  user_id: number;
  workorder_id?: number;
  organization_id: number;
  scheduled_date?: string;
  completed_date?: string;
  duration_hours?: number;
  cost?: number;
  notes?: string;
  created_at: string;
  updated_at?: string;
}

export interface MaintenanceUpdate {
  description?: string;
  status?: string;
  maintenance_type?: string;
  user_id?: number;
  scheduled_date?: string;
  completed_date?: string;
  duration_hours?: number;
  cost?: number;
  notes?: string;
  workorder_id?: number;
}
