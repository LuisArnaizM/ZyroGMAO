export interface Department {
  id: number;
  name: string;
  description?: string | null;
  parent_id?: number | null;
  manager_id?: number | null;
  organization_id: number;
  is_active: boolean;
  created_at: string;
  updated_at?: string | null;
}

export interface DepartmentCreate {
  name: string;
  description?: string;
  parent_id?: number | null;
  manager_id?: number | null;
  organization_id: number;
  is_active?: boolean;
}

export interface DepartmentUpdate {
  name?: string;
  description?: string;
  parent_id?: number | null;
  manager_id?: number | null;
  is_active?: boolean;
}
