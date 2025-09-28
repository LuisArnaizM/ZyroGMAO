/**
 * Tipos para órdenes de trabajo
 */

// Enums específicos para órdenes de trabajo
export enum WorkOrderStatus {
  OPEN = 'OPEN',
  ASSIGNED = 'ASSIGNED',
  IN_PROGRESS = 'IN_PROGRESS',
  COMPLETED = 'COMPLETED',
  CANCELLED = 'CANCELLED'
}

export enum WorkOrderType {
  REPAIR = 'REPAIR',
  INSPECTION = 'INSPECTION',
  MAINTENANCE = 'MAINTENANCE'
}

export enum WorkOrderPriority {
  LOW = 'LOW',
  MEDIUM = 'MEDIUM',
  HIGH = 'HIGH'
}

export interface WorkOrderCreate {
  title: string;
  description?: string;
  work_type?: string;
  status?: string;
  priority?: string;
  estimated_hours?: number;
  estimated_cost?: number;
  scheduled_date?: string;
  asset_id: number;
  assigned_to?: number;
  failure_id?: number;
  maintenance_id?: number;
  plan_id?: number; // vínculo con maintenance_plan
}

export interface WorkOrderRead {
  id: number;
  title: string;
  description?: string;
  work_type: string;
  status: string;
  priority: string;
  estimated_hours?: number;
  actual_hours?: number;
  estimated_cost?: number;
  actual_cost?: number;
  scheduled_date?: string;
  started_date?: string;
  completed_date?: string;
  asset_id: number;
  assigned_to?: number;
  created_by: number;
  failure_id?: number;
  maintenance_id?: number;
  plan_id?: number; // añadido
  organization_id: number;
  created_at: string;
  updated_at?: string;
}

export interface WorkOrderUpdate {
  title?: string;
  description?: string;
  work_type?: string;
  status?: string;
  priority?: string;
  estimated_hours?: number;
  actual_hours?: number;
  estimated_cost?: number;
  actual_cost?: number;
  scheduled_date?: string;
  started_date?: string;
  completed_date?: string;
  assigned_to?: number;
  failure_id?: number;
  maintenance_id?: number;
  plan_id?: number; // añadido
}
