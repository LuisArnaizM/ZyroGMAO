import { ApiClient, apiClient } from '../utils/api-client';

export interface KpiSummary {
  total_workorders: number;
  open_workorders: number;
  in_progress_workorders: number;
  completed_workorders_30d: number;
  overdue_workorders: number;
  planned_pct: number;
  avg_completion_time_hours?: number | null;
  mttr_hours?: number | null;
  mtbf_hours?: number | null;
  mttf_hours?: number | null;
}

export interface KpiTrendPoint {
  label: string;
  created: number;
  completed: number;
}

export interface KpiTrends {
  period: string;
  window: number;
  points: KpiTrendPoint[];
}

export class KpiService {
  constructor(private apiClient: ApiClient) {}

  async getSummary(): Promise<KpiSummary> {
    return this.apiClient.get<KpiSummary>('/kpi/summary');
  }

  async getTrends(weeks = 8): Promise<KpiTrends> {
    return this.apiClient.get<KpiTrends>(`/kpi/trends?weeks=${weeks}`);
  }

  async getAssetsKpi() {
    return this.apiClient.get<{ total: number; active: number; maintenance: number; inactive: number; retired: number; total_value?: number | null }>(`/kpi/assets`);
  }

  async getWorkordersKpi() {
    return this.apiClient.get<{ total: number; draft: number; scheduled: number; in_progress: number; completed: number; cancelled: number; overdue: number }>(`/kpi/workorders`);
  }

  async getFailuresKpi() {
    return this.apiClient.get<{ total: number; pending: number; in_progress: number; resolved: number; critical: number }>(`/kpi/failures`);
  }

  async getMonthlyResponse(months = 6) {
    return this.apiClient.get<{ points: { month: string; avg_response_hours: number | null }[] }>(`/kpi/response/monthly?months=${months}`);
  }
}

export const kpiService = new KpiService(apiClient);
