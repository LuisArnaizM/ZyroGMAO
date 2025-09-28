/**
 * Utilidades para construcción de URLs y parámetros de consulta
 */

import { PaginationParams, FilterParams } from '@/types';

/**
 * Construye una URL con parámetros de consulta
 */
export function buildUrl(endpoint: string, params?: Record<string, unknown>): string {
  if (!params || Object.keys(params).length === 0) {
    return endpoint;
  }

  const searchParams = new URLSearchParams();
  
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== '') {
      searchParams.append(key, String(value));
    }
  });

  const queryString = searchParams.toString();
  return queryString ? `${endpoint}?${queryString}` : endpoint;
}

/**
 * Combina parámetros de paginación y filtros
 */
export function buildQueryParams(
  pagination?: PaginationParams,
  filters?: FilterParams,
  additionalParams?: Record<string, unknown>
): Record<string, unknown> {
  return {
    ...pagination,
    ...filters,
    ...additionalParams,
  };
}

/**
 * Formatea fechas para envío a la API
 */
export function formatDate(date: Date | string): string {
  if (typeof date === 'string') {
    return date;
  }
  return date.toISOString();
}

/**
 * Parsea fechas desde la API
 */
export function parseDate(dateString: string): Date {
  return new Date(dateString);
}

/**
 * Valida formato de email
 */
export function isValidEmail(email: string): boolean {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return emailRegex.test(email);
}

/**
 * Valida slug de organización
 */
export function isValidSlug(slug: string): boolean {
  const slugRegex = /^[a-z0-9-]+$/;
  return slugRegex.test(slug);
}

/**
 * Debounce function para búsquedas
 */
export function debounce<T extends (...args: unknown[]) => unknown>(
  func: T,
  delay: number
): (...args: Parameters<T>) => void {
  let timeoutId: NodeJS.Timeout;
  
  return (...args: Parameters<T>) => {
    clearTimeout(timeoutId);
    timeoutId = setTimeout(() => func(...args), delay);
  };
}
