import { ApiClient, apiClient } from '../utils/api-client';
import { buildUrl, buildQueryParams } from '../utils/helpers';
import { Department, DepartmentCreate, DepartmentUpdate, PaginationParams, UserRead } from '../types';

export class DepartmentService {
  private apiClient: ApiClient;

  constructor(client?: ApiClient) {
    this.apiClient = client || apiClient;
  }

  async create(data: DepartmentCreate): Promise<Department> {
    return this.apiClient.post<Department>('/department/', data);
  }

  async getAll(pagination?: PaginationParams): Promise<Department[]> {
    const params = buildQueryParams(pagination, undefined);
    const url = buildUrl('/department/', params);
    return this.apiClient.get<Department[]>(url);
  }

  async getById(id: number): Promise<Department> {
    return this.apiClient.get<Department>(`/department/${id}`);
  }

  async update(id: number, data: DepartmentUpdate): Promise<Department> {
    return this.apiClient.put<Department>(`/department/${id}` , data);
  }

  async delete(id: number): Promise<void> {
    await this.apiClient.delete(`/department/${id}`);
  }

  async getTechnicians(depId: number): Promise<UserRead[]> {
    return this.apiClient.get<UserRead[]>(`/department/${depId}/technicians`);
  }

  async getUsers(depId: number): Promise<UserRead[]> {
    return this.apiClient.get<UserRead[]>(`/department/${depId}/users`);
  }
}

export const departmentService = new DepartmentService();
