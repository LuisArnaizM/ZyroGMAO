import { useEffect, useCallback } from 'react';
import { useAppDispatch, useAppSelector } from './index';
import { 
  fetchDashboardMetrics, 
  setAutoRefresh, 
  setRefreshInterval, 
  clearError,
  addAlert,
  removeAlert
} from '../slices/dashboardSlice';

// Tipo para las alertas
interface Alert {
  id: string;
  type: 'warning' | 'error' | 'info';
  message: string;
  timestamp: string;
}

export function useDashboard() {
  const dispatch = useAppDispatch();
  const {
    metrics,
    loading,
    error,
    lastUpdated,
    autoRefresh,
    refreshInterval
  } = useAppSelector((state) => state.dashboard); // ✅ Ahora funciona

  // Auto-refresh con intervalo
  useEffect(() => {
    if (!autoRefresh) return;

    const interval = setInterval(() => {
      dispatch(fetchDashboardMetrics());
    }, refreshInterval);

    return () => clearInterval(interval);
  }, [dispatch, autoRefresh, refreshInterval]);

  // Cargar datos iniciales
  useEffect(() => {
    dispatch(fetchDashboardMetrics());
  }, [dispatch]);

  // Funciones helper
  const toggleAutoRefresh = useCallback(() => {
    dispatch(setAutoRefresh(!autoRefresh));
  }, [dispatch, autoRefresh]);

  const updateRefreshInterval = useCallback((interval: number) => {
    dispatch(setRefreshInterval(interval));
  }, [dispatch]);

  const refresh = useCallback(() => {
    dispatch(fetchDashboardMetrics());
  }, [dispatch]);

  const clearDashboardError = useCallback(() => {
    dispatch(clearError());
  }, [dispatch]);

  const addDashboardAlert = useCallback((alert: Alert) => {
    dispatch(addAlert(alert));
  }, [dispatch]);

  const removeDashboardAlert = useCallback((alertId: string) => {
    dispatch(removeAlert(alertId));
  }, [dispatch]);

  return {
    // Estado
    metrics,
    loading,
    error,
    lastUpdated,
    autoRefresh,
    refreshInterval,
    
    // Acciones
    toggleAutoRefresh,
    updateRefreshInterval,
    refresh,
    clearError: clearDashboardError,
    addAlert: addDashboardAlert,
    removeAlert: removeDashboardAlert,
  };
}