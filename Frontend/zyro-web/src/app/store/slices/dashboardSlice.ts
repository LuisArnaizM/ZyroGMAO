import { createSlice, createAsyncThunk, PayloadAction } from '@reduxjs/toolkit';
import { assetService } from '@/services/asset.service';

// Tipos para las métricas del dashboard
interface DashboardMetrics {
  machines: {
    total: number;
    operational: number;
    maintenance: number;
    broken: number;
    outOfService: number;
  };
  workOrders: {
    pending: number;
    inProgress: number;
    completed: number;
    overdue: number;
  };
  assets: {
    total: number;
    byLocation: Record<string, number>;
    byResponsible: Record<string, number>;
  };
  alerts: Array<{
    id: string;
    type: 'warning' | 'error' | 'info';
    message: string;
    timestamp: string;
  }>;
}

interface DashboardState {
  metrics: DashboardMetrics | null;
  loading: boolean;
  error: string | null;
  lastUpdated: string | null;
  autoRefresh: boolean;
  refreshInterval: number; // en milisegundos
}

// Estado inicial
const initialState: DashboardState = {
  metrics: null,
  loading: false,
  error: null,
  lastUpdated: null,
  autoRefresh: true,
  refreshInterval: 30000, // 30 segundos
};

// Async thunk para cargar métricas del dashboard
export const fetchDashboardMetrics = createAsyncThunk(
  'dashboard/fetchMetrics',
  async (_, { rejectWithValue }) => {
    try {
      // Aquí harías llamadas a tus servicios
      const [assetStats] = await Promise.all([
        assetService.getStats(),
        // Agregar más llamadas cuando tengas los servicios
      ]);
      
      return {
        machines: {
          total: 0,
          operational: 0,
          maintenance: 0,
          broken: 0,
          outOfService: 0,
        },
        workOrders: {
          pending: 0,
          inProgress: 0,
          completed: 0,
          overdue: 0,
        },
        assets: {
          total: assetStats.total,
          byLocation: {}, // Se podría calcular desde los assets individuales
          byResponsible: {}, // Se podría calcular desde los assets individuales
        },
        alerts: [],
      } as DashboardMetrics;
    } catch (error: unknown) {
      const errorMessage = error instanceof Error ? error.message : 'Error loading dashboard metrics';
      return rejectWithValue(errorMessage);
    }
  }
);

// Slice del dashboard
const dashboardSlice = createSlice({
  name: 'dashboard',
  initialState,
  reducers: {
    // Configurar auto-refresh
    setAutoRefresh: (state, action: PayloadAction<boolean>) => {
      state.autoRefresh = action.payload;
    },
    
    // Configurar intervalo de refresco
    setRefreshInterval: (state, action: PayloadAction<number>) => {
      state.refreshInterval = action.payload;
    },
    
    // Limpiar error
    clearError: (state) => {
      state.error = null;
    },
    
    // Actualización en tiempo real (vía WebSocket en el futuro)
    updateMetricsRealTime: (state, action: PayloadAction<Partial<DashboardMetrics>>) => {
      if (state.metrics) {
        state.metrics = { ...state.metrics, ...action.payload };
        state.lastUpdated = new Date().toISOString();
      }
    },
    
    // Agregar nueva alerta
    addAlert: (state, action: PayloadAction<DashboardMetrics['alerts'][0]>) => {
      if (state.metrics) {
        state.metrics.alerts.unshift(action.payload);
        // Mantener solo las últimas 10 alertas
        if (state.metrics.alerts.length > 10) {
          state.metrics.alerts = state.metrics.alerts.slice(0, 10);
        }
      }
    },
    
    // Remover alerta
    removeAlert: (state, action: PayloadAction<string>) => {
      if (state.metrics) {
        state.metrics.alerts = state.metrics.alerts.filter(
          alert => alert.id !== action.payload
        );
      }
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(fetchDashboardMetrics.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(fetchDashboardMetrics.fulfilled, (state, action) => {
        state.loading = false;
        state.metrics = action.payload;
        state.lastUpdated = new Date().toISOString();
      })
      .addCase(fetchDashboardMetrics.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload as string;
      });
  },
});

// Exportar acciones
export const {
  setAutoRefresh,
  setRefreshInterval,
  clearError,
  updateMetricsRealTime,
  addAlert,
  removeAlert,
} = dashboardSlice.actions;

// Exportar reducer
export default dashboardSlice.reducer;