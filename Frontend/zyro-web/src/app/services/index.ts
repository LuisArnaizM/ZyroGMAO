// Service exports
export { AuthService } from './auth.service';
export { UserService } from './user.service';
export { OrganizationService } from './organization.service';
export { AssetService } from './asset.service';
export { ComponentService } from './component.service';
export { SensorService } from './sensor.service';
export { FailureService } from './failure.service';
export { MaintenanceService } from './maintenance.service';
export { MaintenancePlanService } from './maintenancePlan.service';
export { TaskService } from './task.service';
export { WorkOrderService } from './workorder.service';
export { InventoryService } from './inventory.service';

// Main API client factory
import { ApiClient } from '../utils/api-client';
import { AuthService } from './auth.service';
import { UserService } from './user.service';
import { OrganizationService } from './organization.service';
import { AssetService } from './asset.service';
import { ComponentService } from './component.service';
import { SensorService } from './sensor.service';
import { FailureService } from './failure.service';
import { MaintenanceService } from './maintenance.service';
import { MaintenancePlanService } from './maintenancePlan.service';
import { TaskService } from './task.service';
import { WorkOrderService } from './workorder.service';
import { InventoryService } from './inventory.service';

/**
 * Main API client that provides access to all services
 */
export class IndustrialMaintenanceAPI {
  private apiClient: ApiClient;
  
  // Service instances
  public readonly auth: AuthService;
  public readonly users: UserService;
  public readonly organizations: OrganizationService;
  public readonly assets: AssetService;
  public readonly components: ComponentService;
  public readonly sensors: SensorService;
  public readonly failures: FailureService;
  public readonly maintenance: MaintenanceService;
  public readonly maintenancePlan: MaintenancePlanService;
  public readonly tasks: TaskService;
  public readonly workOrders: WorkOrderService;
  public readonly inventory: InventoryService;

  constructor(baseUrl: string = 'http://localhost:8000/v1') {
    this.apiClient = new ApiClient({ baseURL: baseUrl });
    
    // Initialize all services
    this.auth = new AuthService();
    this.users = new UserService(this.apiClient);
    this.organizations = new OrganizationService();
    this.assets = new AssetService();
    this.components = new ComponentService();
    this.sensors = new SensorService();
    this.failures = new FailureService();
    this.maintenance = new MaintenanceService();
    this.maintenancePlan = new MaintenancePlanService();
    this.tasks = new TaskService(this.apiClient);
    this.workOrders = new WorkOrderService(this.apiClient);
  this.inventory = new InventoryService(this.apiClient);
  }

  /**
   * Set the authentication token for all requests
   */
  setAuthToken(token: string, refreshToken?: string): void {
    this.apiClient.setTokens(token, refreshToken);
  }

  /**
   * Clear the authentication token
   */
  clearAuthToken(): void {
    this.apiClient.clearTokens();
  }

  /**
   * Get the current authentication token
   */
  getAuthToken(): string | null {
    return this.apiClient['accessToken'] || null;
  }

  /**
   * Update the base URL for the API
   */
  updateBaseUrl(baseUrl: string): void {
    this.apiClient['baseURL'] = baseUrl;
  }

  /**
   * Check if the client is authenticated
   */
  isAuthenticated(): boolean {
    return this.apiClient['accessToken'] !== null;
  }
}
