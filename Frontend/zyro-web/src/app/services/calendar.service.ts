import { ApiClient, apiClient } from '../utils/api-client';

export interface WorkingDayPattern {
  weekday: number; // 0-6
  hours: number;
  is_active: boolean;
}
export interface SpecialDay {
  id?: number;
  date: string; // YYYY-MM-DD
  is_working: boolean;
  hours?: number | null;
  reason?: string | null;
}
export interface VacationRangeCreate { start_date: string; end_date: string; reason?: string | null; }
export interface TeamVacationDay { id: number; user_id: number; first_name: string; last_name: string; date: string; reason?: string | null; }

export class CalendarService {
  constructor(private client: ApiClient = apiClient) {}

  getPattern(userId: number) {
    return this.client.get<WorkingDayPattern[]>(`/calendar/${userId}/pattern`);
  }
  updatePattern(userId: number, pattern: WorkingDayPattern[]) {
    return this.client.put<WorkingDayPattern[]>(`/calendar/${userId}/pattern`, pattern);
  }
  listSpecial(userId: number, start: string, end: string) {
    return this.client.get<SpecialDay[]>(`/calendar/${userId}/special?start=${start}&end=${end}`);
  }
  addSpecial(userId: number, data: Omit<SpecialDay,'id'>) {
    return this.client.post<SpecialDay>(`/calendar/${userId}/special`, data);
  }
  deleteSpecial(userId: number, specialId: number) {
    return this.client.delete(`/calendar/${userId}/special/${specialId}`);
  }
  addVacationRange(userId: number, data: VacationRangeCreate) {
    return this.client.post<SpecialDay[]>(`/calendar/${userId}/vacations`, data);
  }
  listTeamVacations(managerId: number, start: string, end: string) {
    return this.client.get<TeamVacationDay[]>(`/calendar/team/${managerId}/vacations?start=${start}&end=${end}`);
  }
}

export const calendarService = new CalendarService();
