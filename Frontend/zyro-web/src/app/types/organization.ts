/**
 * Tipos para organizaciones
 */

export interface OrganizationCreate {
  name: string;
  slug: string;
  description?: string;
  domain?: string;
  max_users?: number;
  max_assets?: number;
}

export interface OrganizationRead {
  id: number;
  name: string;
  slug: string;
  description?: string;
  domain?: string;
  is_active: boolean;
  max_users: number;
  max_assets: number;
  created_at: string;
  updated_at?: string;
}

export interface OrganizationUpdate {
  name?: string;
  description?: string;
  domain?: string;
  is_active?: boolean;
  max_users?: number;
  max_assets?: number;
}

export interface OrganizationStats {
  id: number;
  name: string;
  slug: string;
  user_count: number;
  asset_count: number;
  machine_count: number;
  active_tasks: number;
  pending_failures: number;
  max_users: number;
  max_assets: number;
}
