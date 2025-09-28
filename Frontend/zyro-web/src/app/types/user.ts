/**
 * Tipos para usuarios
 */
import { Role } from './base';

export interface UserCreate {
  username: string;
  first_name: string;
  last_name: string;
  email: string;
  password: string;
  role: Role;
  organization_id?: number;
  department_id?: number;
}

export interface UserRead {
  id: number;
  username: string;
  first_name: string;
  last_name: string;
  email: string;
  role: Role;
  is_active: number;
  organization_id?: number;
  department_id?: number;
  created_at: string;
  updated_at?: string;
}

export interface UserUpdate {
  username?: string;
  first_name?: string;
  last_name?: string;
  email?: string;
  role?: Role;
  is_active?: number;
  organization_id?: number;
  department_id?: number;
}
