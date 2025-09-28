import { ApiClient } from '../utils/api-client';
import {
  WorkOrderRead,
  WorkOrderCreate,
  WorkOrderUpdate,
  PaginationParams,
  ApiResponse
} from '../types';

export class WorkOrderService {
  constructor(private apiClient: ApiClient) {}

  /**
   * Get all work orders with optional filtering
   */
  async getWorkOrders(params?: {
    pagination?: PaginationParams;
    asset_id?: string;
    assigned_to?: string;
    created_by?: string;
    status?: string;
    priority?: string;
    work_type?: string;
    scheduled_date_from?: string;
    scheduled_date_to?: string;
  }): Promise<ApiResponse<WorkOrderRead[]>> {
    const queryParams = new URLSearchParams();
    
    if (params?.pagination) {
      if (params.pagination.page) queryParams.append('page', params.pagination.page.toString());
      if (params.pagination.page_size) queryParams.append('page_size', params.pagination.page_size.toString());
    }
    if (params?.asset_id) queryParams.append('asset_id', params.asset_id);
    if (params?.assigned_to) queryParams.append('assigned_to', params.assigned_to);
    if (params?.created_by) queryParams.append('created_by', params.created_by);
    if (params?.status) queryParams.append('status', params.status);
    if (params?.priority) queryParams.append('priority', params.priority);
    if (params?.work_type) queryParams.append('work_type', params.work_type);
    if (params?.scheduled_date_from) queryParams.append('scheduled_date_from', params.scheduled_date_from);
    if (params?.scheduled_date_to) queryParams.append('scheduled_date_to', params.scheduled_date_to);

    const url = queryParams.toString() ? `/workorders/?${queryParams}` : '/workorders/';
    const data = await this.apiClient.get<WorkOrderRead[]>(url);
    return { success: true, data };
  }

  /**
   * Get work order by ID
   */
  async getWorkOrder(id: number): Promise<ApiResponse<WorkOrderRead>> {
    const data = await this.apiClient.get<WorkOrderRead>(`/workorders/${id}`);
    return { success: true, data };
  }

  /**
   * Create a new work order
   */
  async createWorkOrder(workorderData: WorkOrderCreate): Promise<ApiResponse<WorkOrderRead>> {
    const data = await this.apiClient.post<WorkOrderRead>('/workorders/', workorderData);
    return { success: true, data };
  }

  /**
   * Update an existing work order
   */
  async updateWorkOrder(id: number, workorderData: WorkOrderUpdate): Promise<ApiResponse<WorkOrderRead>> {
    const data = await this.apiClient.put<WorkOrderRead>(`/workorders/${id}`, workorderData);
    return { success: true, data };
  }

  /**
   * Delete a work order
   */
  async deleteWorkOrder(id: number): Promise<ApiResponse<void>> {
    await this.apiClient.delete(`/workorders/${id}`);
    return { success: true, data: undefined };
  }

  /**
   * Complete a work order
   */
  async completeWorkOrder(id: number, payload?: { maintenance_notes?: string }): Promise<ApiResponse<WorkOrderRead>> {
    const result = await this.apiClient.post<WorkOrderRead>(`/workorders/${id}/complete`, payload || {});
    return { success: true, data: result };
  }

  /**
   * Get work order statistics
   */
  async getWorkOrderStats(): Promise<ApiResponse<{
    total: number;
    pending: number;
    in_progress: number;
    completed: number;
    cancelled: number;
  }>> {
    // Por ahora simularemos las estadísticas ya que el endpoint puede no existir
    const workOrders = await this.getWorkOrders();
    if (workOrders.success && workOrders.data) {
      const total = workOrders.data.length;
      // Backend enums: OPEN, ASSIGNED, IN_PROGRESS, COMPLETED, CANCELLED
      const pending = workOrders.data.filter(wo => wo.status === 'OPEN' || wo.status === 'ASSIGNED').length;
      const in_progress = workOrders.data.filter(wo => wo.status === 'IN_PROGRESS').length;
      const completed = workOrders.data.filter(wo => wo.status === 'COMPLETED').length;
      const cancelled = workOrders.data.filter(wo => wo.status === 'CANCELLED').length;

      return {
        success: true,
        data: { total, pending, in_progress, completed, cancelled }
      };
    }
    
    return { 
      success: true, 
      data: { total: 0, pending: 0, in_progress: 0, completed: 0, cancelled: 0 } 
    };
  }
}