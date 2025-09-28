import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import { kpiService } from '@/services/kpi.service';

export interface AssetKpi { total: number; active: number; maintenance: number; inactive: number; retired: number; total_value?: number | null }
export interface WorkOrderKpi { total: number; draft: number; scheduled: number; in_progress: number; completed: number; cancelled: number; overdue: number }
export interface FailureKpi { total: number; pending: number; in_progress: number; resolved: number; critical: number }

interface KpiState {
  assets: AssetKpi | null;
  workorders: WorkOrderKpi | null;
  failures: FailureKpi | null;
  loading: boolean;
  error: string | null;
}

const initialState: KpiState = {
  assets: null,
  workorders: null,
  failures: null,
  loading: false,
  error: null,
};

export const fetchAssetsKpi = createAsyncThunk('kpi/assets', async (_, { rejectWithValue }) => {
  try { return await kpiService.getAssetsKpi(); } catch (e: unknown) { const msg = e instanceof Error ? e.message : 'Error KPIs assets'; return rejectWithValue(msg); }
});
export const fetchWorkordersKpi = createAsyncThunk('kpi/workorders', async (_, { rejectWithValue }) => {
  try { return await kpiService.getWorkordersKpi(); } catch (e: unknown) { const msg = e instanceof Error ? e.message : 'Error KPIs workorders'; return rejectWithValue(msg); }
});
export const fetchFailuresKpi = createAsyncThunk('kpi/failures', async (_, { rejectWithValue }) => {
  try { return await kpiService.getFailuresKpi(); } catch (e: unknown) { const msg = e instanceof Error ? e.message : 'Error KPIs failures'; return rejectWithValue(msg); }
});

const kpiSlice = createSlice({
  name: 'kpi',
  initialState,
  reducers: {},
  extraReducers: (builder) => {
    builder
      .addCase(fetchAssetsKpi.pending, (s) => { s.loading = true; s.error = null; })
      .addCase(fetchAssetsKpi.fulfilled, (s, a) => { s.loading = false; s.assets = a.payload as AssetKpi; })
      .addCase(fetchAssetsKpi.rejected, (s, a) => { s.loading = false; s.error = a.payload as string; })
      .addCase(fetchWorkordersKpi.pending, (s) => { s.loading = true; s.error = null; })
      .addCase(fetchWorkordersKpi.fulfilled, (s, a) => { s.loading = false; s.workorders = a.payload as WorkOrderKpi; })
      .addCase(fetchWorkordersKpi.rejected, (s, a) => { s.loading = false; s.error = a.payload as string; })
      .addCase(fetchFailuresKpi.pending, (s) => { s.loading = true; s.error = null; })
      .addCase(fetchFailuresKpi.fulfilled, (s, a) => { s.loading = false; s.failures = a.payload as FailureKpi; })
      .addCase(fetchFailuresKpi.rejected, (s, a) => { s.loading = false; s.error = a.payload as string; });
  }
});

export default kpiSlice.reducer;
