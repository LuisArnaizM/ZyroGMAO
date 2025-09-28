import { ApiClient } from '../utils/api-client';
import { apiClient } from '../utils/api-client';

export interface PlannerTask {
  id: number;
  title: string;
  estimated_hours?: number;
  status: string;
  priority?: string;
  due_date?: string;
}

export interface PlannerDay {
  date: string; // ISO date
  capacity_hours: number;
  planned_hours: number;
  free_hours: number;
  tasks: PlannerTask[];
  is_non_working?: boolean | null;
  reason?: string | null;
}

export interface PlannerUserRow {
  user: { id: number; first_name: string; last_name: string; role: string };
  days: PlannerDay[];
}

export interface PlannerWeek {
  start: string; // ISO date (monday)
  days: number;
  users: PlannerUserRow[];
}

export class PlannerService {
  constructor(private client: ApiClient = apiClient) {}

  async getWeek(params?: { start?: string; days?: number }): Promise<PlannerWeek> {
    const sp = new URLSearchParams();
    if (params?.start) sp.append('start', params.start);
    if (params?.days) sp.append('days', String(params.days));
    const url = sp.toString() ? `/planner/week?${sp}` : '/planner/week';
    return this.client.get<PlannerWeek>(url);
  }
}

export const plannerService = new PlannerService();
