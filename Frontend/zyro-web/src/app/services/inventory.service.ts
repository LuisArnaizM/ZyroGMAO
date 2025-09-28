import { ApiClient } from '../utils/api-client';
import { InventoryItemCreate, InventoryItemRead, InventoryItemUpdate, TaskUsedComponentRead, InventoryItemReadWithComponent } from '../types/inventory';

export class InventoryService {
  constructor(private apiClient: ApiClient) {}

  async create(item: InventoryItemCreate): Promise<InventoryItemRead> {
    return this.apiClient.post<InventoryItemRead>('/inventory/', item);
    }
  async list(component_type?: string): Promise<InventoryItemReadWithComponent[]> {
    const url = component_type ? `/inventory/?component_type=${encodeURIComponent(component_type)}` : '/inventory/';
    return this.apiClient.get<InventoryItemReadWithComponent[]>(url);
  }
  async get(itemId: number): Promise<InventoryItemReadWithComponent> {
    return this.apiClient.get<InventoryItemReadWithComponent>(`/inventory/${itemId}`);
  }
  async getByComponent(componentId: number): Promise<InventoryItemReadWithComponent> {
    return this.apiClient.get<InventoryItemReadWithComponent>(`/inventory/by-component/${componentId}`);
  }
  async update(itemId: number, data: InventoryItemUpdate): Promise<InventoryItemRead> {
    return this.apiClient.put<InventoryItemRead>(`/inventory/${itemId}`, data);
  }
  async remove(itemId: number): Promise<{ status: string }> {
    return this.apiClient.delete<{ status: string }>(`/inventory/${itemId}`);
  }
  async adjust(itemId: number, delta: number, reason?: string): Promise<InventoryItemRead> {
    return this.apiClient.post<InventoryItemRead>(`/inventory/${itemId}/adjust`, { delta, reason });
  }
  async listUsage(componentId?: number): Promise<TaskUsedComponentRead[]> {
    const url = componentId ? `/inventory/usage/?component_id=${componentId}` : '/inventory/usage/';
    return this.apiClient.get<TaskUsedComponentRead[]>(url);
  }
}
