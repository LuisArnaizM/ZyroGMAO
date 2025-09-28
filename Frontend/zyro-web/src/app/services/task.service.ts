import { ApiClient } from '../utils/api-client';
import {
  TaskRead,
  TaskCreate,
  TaskUpdate,
  TaskStatus,
  TaskPriority,
  PaginationParams,
  ApiResponse
} from '../types';

export class TaskService {
  constructor(private apiClient: ApiClient) {}

  /**
   * Get all tasks with optional filtering
   */
  async getTasks(params?: {
    pagination?: PaginationParams;
    asset_id?: string;
    work_order_id?: string;
    component_id?: string;
    assigned_to?: string;
    status?: TaskStatus;
    priority?: TaskPriority;
    due_date_from?: string;
    due_date_to?: string;
  }): Promise<ApiResponse<TaskRead[]>> {
    const queryParams = new URLSearchParams();
    
    if (params?.pagination) {
      if (params.pagination.page) queryParams.append('page', params.pagination.page.toString());
      if (params.pagination.page_size) queryParams.append('page_size', params.pagination.page_size.toString());
    }
    if (params?.asset_id) queryParams.append('asset_id', params.asset_id);
    if (params?.work_order_id) queryParams.append('work_order_id', params.work_order_id);
    if (params?.component_id) queryParams.append('component_id', params.component_id);
    if (params?.assigned_to) queryParams.append('assigned_to', params.assigned_to);
    if (params?.status) queryParams.append('status', params.status);
    if (params?.priority) queryParams.append('priority', params.priority);
    if (params?.due_date_from) queryParams.append('due_date_from', params.due_date_from);
    if (params?.due_date_to) queryParams.append('due_date_to', params.due_date_to);

    const url = queryParams.toString() ? `/tasks/?${queryParams}` : '/tasks/';
    const data = await this.apiClient.get<TaskRead[]>(url);
    return { success: true, data };
  }

  /**
   * Get task by ID
   */
  async getTask(taskId: string): Promise<ApiResponse<TaskRead>> {
    const data = await this.apiClient.get<TaskRead>(`/tasks/${taskId}`);
    return { success: true, data };
  }

  /**
   * Create a new task
   */
  async createTask(taskData: TaskCreate): Promise<ApiResponse<TaskRead>> {
    const data = await this.apiClient.post<TaskRead>('/tasks/', taskData);
    return { success: true, data };
  }

  /**
   * Update an existing task
   */
  async updateTask(taskId: string, taskData: TaskUpdate): Promise<ApiResponse<TaskRead>> {
    const data = await this.apiClient.patch<TaskRead>(`/tasks/${taskId}`, taskData);
    return { success: true, data };
  }

  /**
   * Delete a task
   */
  async deleteTask(taskId: string): Promise<ApiResponse<void>> {
    await this.apiClient.delete<void>(`/tasks/${taskId}`);
    return { success: true };
  }

  /**
   * Complete a task
   */
  async completeTask(
    taskId: string,
    data?: {
      notes?: string;
      description?: string;
      actual_hours?: number;
      used_components?: { component_id: number; quantity: number }[];
    }
  ): Promise<ApiResponse<TaskRead>> {
    // Nuevo flujo: usar endpoint dedicado de completar tarea (ajusta inventario y registra uso)
    const result = await this.apiClient.post<TaskRead>(`/tasks/${taskId}/complete`, data || {});
    return { success: true, data: result };
  }

  /**
   * Assign task to user
   */
  async assignTask(taskId: string, userId: string): Promise<ApiResponse<TaskRead>> {
    const data = await this.apiClient.patch<TaskRead>(`/tasks/${taskId}`, {
      assigned_to: userId
    });
    return { success: true, data };
  }

  /**
   * Update task priority
   */
  async updateTaskPriority(taskId: string, priority: TaskPriority): Promise<ApiResponse<TaskRead>> {
    const data = await this.apiClient.patch<TaskRead>(`/tasks/${taskId}`, {
      priority
    });
    return { success: true, data };
  }

  /**
   * Get tasks assigned to a specific user
   */
  async getTasksByUser(userId: string, params?: {
    pagination?: PaginationParams;
    status?: TaskStatus;
    priority?: TaskPriority;
  }): Promise<ApiResponse<TaskRead[]>> {
    const queryParams = new URLSearchParams();
    queryParams.append('assigned_to', userId);
    
    if (params?.pagination) {
      if (params.pagination.page) queryParams.append('page', params.pagination.page.toString());
      if (params.pagination.page_size) queryParams.append('page_size', params.pagination.page_size.toString());
    }
    if (params?.status) queryParams.append('status', params.status);
    if (params?.priority) queryParams.append('priority', params.priority);

    const data = await this.apiClient.get<TaskRead[]>(`/tasks/?${queryParams}`);
    return { success: true, data };
  }

  /**
   * Get tasks for a specific asset
   */
  async getTasksByAsset(assetId: string, params?: {
    pagination?: PaginationParams;
    status?: TaskStatus;
  }): Promise<ApiResponse<TaskRead[]>> {
    const queryParams = new URLSearchParams();
    queryParams.append('asset_id', assetId);
    
    if (params?.pagination) {
      if (params.pagination.page) queryParams.append('page', params.pagination.page.toString());
      if (params.pagination.page_size) queryParams.append('page_size', params.pagination.page_size.toString());
    }
    if (params?.status) queryParams.append('status', params.status);

    const data = await this.apiClient.get<TaskRead[]>(`/tasks/?${queryParams}`);
    return { success: true, data };
  }

  /**
   * Get tasks for a specific work order
   */
  async getTasksByWorkOrder(workOrderId: string, params?: {
    pagination?: PaginationParams;
    status?: TaskStatus;
  }): Promise<ApiResponse<TaskRead[]>> {
    const queryParams = new URLSearchParams();
    queryParams.append('work_order_id', workOrderId);
    
    if (params?.pagination) {
      if (params.pagination.page) queryParams.append('page', params.pagination.page.toString());
      if (params.pagination.page_size) queryParams.append('page_size', params.pagination.page_size.toString());
    }
    if (params?.status) queryParams.append('status', params.status);

    const data = await this.apiClient.get<TaskRead[]>(`/tasks/?${queryParams}`);
    return { success: true, data };
  }

  /**
   * Get overdue tasks
   */
  async getOverdueTasks(params?: PaginationParams): Promise<ApiResponse<TaskRead[]>> {
    const today = new Date().toISOString().split('T')[0];
    const queryParams = new URLSearchParams();
    queryParams.append('due_date_to', today);
    queryParams.append('status', TaskStatus.PENDING);
    
    if (params?.page) queryParams.append('page', params.page.toString());
    if (params?.page_size) queryParams.append('page_size', params.page_size.toString());

    const data = await this.apiClient.get<TaskRead[]>(`/tasks/?${queryParams}`);
    return { success: true, data };
  }

  /**
   * Get task statistics
   */
  async getTaskStatistics(params?: {
    asset_id?: string;
    work_order_id?: string;
    assigned_to?: string;
    date_from?: string;
    date_to?: string;
  }): Promise<ApiResponse<{
    total: number;
    pending: number;
    in_progress: number;
    completed: number;
    cancelled: number;
    overdue: number;
    by_priority: Record<TaskPriority, number>;
  }>> {
    const queryParams = new URLSearchParams();
    
    if (params?.asset_id) queryParams.append('asset_id', params.asset_id);
    if (params?.work_order_id) queryParams.append('work_order_id', params.work_order_id);
    if (params?.assigned_to) queryParams.append('assigned_to', params.assigned_to);
    if (params?.date_from) queryParams.append('date_from', params.date_from);
    if (params?.date_to) queryParams.append('date_to', params.date_to);

    const url = queryParams.toString() ? `/tasks/statistics?${queryParams}` : '/tasks/statistics';
    const data = await this.apiClient.get<{
      total: number;
      pending: number;
      in_progress: number;
      completed: number;
      cancelled: number;
      overdue: number;
      by_priority: Record<TaskPriority, number>;
    }>(url);
    return { success: true, data };
  }
}
