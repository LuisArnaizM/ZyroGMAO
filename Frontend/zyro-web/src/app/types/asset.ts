/**
 * Tipos para activos
 */

export interface AssetCreate {
  name: string;
  description?: string;
  asset_type: string;
  model?: string;
  serial_number?: string;
  location?: string;
  status?: string;
  purchase_cost?: number;
  current_value?: number;
  responsible_id?: number;
  purchase_date?: string;
  warranty_expiry?: string;
}

export interface AssetRead {
  id: number;
  name: string;
  description?: string;
  asset_type: string;
  model?: string;
  serial_number?: string;
  location?: string;
  status: string;
  purchase_cost?: number;
  current_value?: number;
  responsible_id?: number;
  organization_id: number;
  created_at: string;
  updated_at?: string;
  purchase_date?: string;
  warranty_expiry?: string;
}

export interface AssetUpdate {
  name?: string;
  description?: string;
  asset_type?: string;
  model?: string;
  serial_number?: string;
  location?: string;
  status?: string;
  purchase_cost?: number;
  current_value?: number;
  responsible_id?: number;
  purchase_date?: string;
  warranty_expiry?: string;
}
