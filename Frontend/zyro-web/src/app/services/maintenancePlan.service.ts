import { ApiClient, apiClient } from '../utils/api-client';

export interface MaintenancePlanCreate {
  name: string;
  description?: string;
  plan_type?: 'PREVENTIVE' | 'CORRECTIVE' | 'INSPECTION' | 'PREDICTIVE';
  frequency_days?: number;
  frequency_weeks?: number;
  frequency_months?: number;
  estimated_duration?: number;
  estimated_cost?: number;
  start_date?: string;
  next_due_date?: string;
  last_execution_date?: string;
  active?: boolean;
  asset_id?: number;
  component_id?: number;
}

export interface MaintenancePlanRead extends MaintenancePlanCreate {
  id: number;
  created_at: string;
  updated_at?: string | null;
}

export class MaintenancePlanService {
  private apiClient: ApiClient;
  base = '/maintenance/plans';

  constructor(client?: ApiClient) {
    this.apiClient = client || apiClient;
  }

  async getByAsset(assetId: number): Promise<MaintenancePlanRead[]> {
    return this.apiClient.get<MaintenancePlanRead[]>(`${this.base}?asset_id=${assetId}`);
  }

  async create(payload: MaintenancePlanCreate): Promise<MaintenancePlanRead> {
    return this.apiClient.post<MaintenancePlanRead>(`${this.base}/`, payload);
  }

  async getUpcoming(params?: { window_days?: number; asset_id?: number; show_blocked?: boolean }): Promise<MaintenancePlanRead[]> {
    const qp = new URLSearchParams();
    if (params?.window_days) qp.append('window_days', String(params.window_days));
    if (params?.asset_id) qp.append('asset_id', String(params.asset_id));
    if (params?.show_blocked) qp.append('show_blocked', 'true');
    const suffix = qp.toString() ? `?${qp.toString()}` : '';
    return this.apiClient.get<MaintenancePlanRead[]>(`${this.base}/upcoming${suffix}`);
  }

  async update(id: number, payload: Partial<MaintenancePlanCreate>): Promise<MaintenancePlanRead> {
    return this.apiClient.put<MaintenancePlanRead>(`${this.base}/${id}`, payload);
  }

  async delete(id: number): Promise<void> {
    await this.apiClient.delete<void>(`${this.base}/${id}`);
  }
}

export const maintenancePlanService = new MaintenancePlanService();
