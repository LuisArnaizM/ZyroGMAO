import type { ComponentRead } from './component';

export interface InventoryItemRead {
  id: number;
  component_id: number;
  quantity: number;
  unit_cost?: number | null;
  created_at?: string | null;
  updated_at?: string | null;
}

export interface InventoryItemCreate {
  component_id: number;
  quantity: number;
  unit_cost?: number | null;
}

export interface InventoryItemUpdate {
  quantity?: number;
  unit_cost?: number | null;
}

export interface TaskUsedComponentRead {
  id: number;
  task_id: number;
  component_id?: number | null;
  quantity: number;
  unit_cost_snapshot?: number | null;
  created_at: string;
}

// Nuevas respuestas GET con componente anidado
export interface InventoryItemReadWithComponent {
  id: number;
  quantity: number;
  unit_cost?: number | null;
  created_at?: string | null;
  updated_at?: string | null;
  component: ComponentRead;
}
