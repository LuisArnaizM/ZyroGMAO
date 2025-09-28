/**
 * Tipos para fallos
 */

export interface FailureCreate {
  description: string;
  asset_id?: number;
  component_id?: number;
  severity?: string;
}

export interface FailureRead {
  id: number;
  description: string;
  status: string;
  severity: string;
  asset_id?: number;
  component_id?: number;
  reported_by: number;
  organization_id: number;
  reported_date: string;
  resolved_date?: string;
  resolution_notes?: string;
  created_at: string;
  updated_at?: string;
}

export interface FailureUpdate {
  description?: string;
  status?: string;
  severity?: string;
  resolved_date?: string;
  resolution_notes?: string;
}

export interface FailureWithWorkOrder extends FailureRead {
  workorder_id?: number;
}
