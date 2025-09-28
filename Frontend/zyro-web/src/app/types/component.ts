/**
 * Tipos para componentes
 */

export interface ComponentCreate {
  name: string;
  description?: string;
  component_type: string;
  model?: string;
  serial_number?: string;
  location?: string;
  status?: string;
  purchase_cost?: number;
  current_value?: number;
  maintenance_interval_days?: number;
  responsible_id?: number;
  asset_id: number;
  installed_date?: string;
  warranty_expiry?: string;
}

export interface ComponentRead {
  name: string;
  description?: string;
  component_type: string;
  model?: string;
  serial_number?: string;
  location?: string;
  status: string;
  purchase_cost?: number;
  current_value?: number;
  maintenance_interval_days?: number;
  responsible_id?: number;
  id: number;
  asset_id: number;
  organization_id: number;
  created_at: string;
  updated_at?: string;
  installed_date?: string;
  warranty_expiry?: string;
  last_maintenance_date?: string;
}

export interface ComponentUpdate {
  name?: string;
  description?: string;
  component_type?: string;
  model?: string;
  serial_number?: string;
  location?: string;
  status?: string;
  purchase_cost?: number;
  current_value?: number;
  maintenance_interval_days?: number;
  responsible_id?: number;
  installed_date?: string;
  warranty_expiry?: string;
  last_maintenance_date?: string;
}

export interface ComponentDetail extends ComponentRead {
  responsible_name?: string;
  total_sensors?: number;
  total_failures?: number;
  total_maintenance_records?: number;
  total_tasks?: number;
  needs_maintenance?: boolean;
  days_since_last_maintenance?: number;
}
