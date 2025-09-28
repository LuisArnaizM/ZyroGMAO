/**
 * Tipos para tareas
 */

// Enums específicos para tareas
export enum TaskStatus {
  PENDING = 'PENDING',
  IN_PROGRESS = 'IN_PROGRESS',
  COMPLETED = 'COMPLETED',
  CANCELLED = 'CANCELLED'
}

export enum TaskPriority {
  LOW = 'LOW',
  MEDIUM = 'MEDIUM',
  HIGH = 'HIGH',
  CRITICAL = 'CRITICAL'
}

export interface TaskCreate {
  title: string;
  description?: string;
  status?: TaskStatus;
  priority?: TaskPriority;
  due_date?: string;
  estimated_hours?: number;
  completion_notes?: string;
  assigned_to?: number;
  asset_id?: number;
  component_id?: number;
  workorder_id?: number;
}

export interface TaskRead {
  id: number;
  title: string;
  description?: string;
  status: TaskStatus;
  priority: TaskPriority;
  due_date?: string;
  estimated_hours?: number;
  actual_hours?: number;
  completion_notes?: string;
  assigned_to?: number;
  asset_id?: number;
  component_id?: number;
  workorder_id?: number;
  created_by_id: number;
  created_at: string;
  updated_at?: string;
}

export interface TaskUsedComponentIn {
  component_id: number;
  quantity: number;
}

export interface TaskUpdate {
  title?: string;
  description?: string;
  status?: TaskStatus;
  priority?: TaskPriority;
  due_date?: string;
  estimated_hours?: number;
  actual_hours?: number;
  completion_notes?: string;
  assigned_to?: number;
  asset_id?: number;
  component_id?: number;
  workorder_id?: number;
  // Al actualizar (por ejemplo al completar), se pueden enviar componentes usados
  used_components?: TaskUsedComponentIn[];
}
