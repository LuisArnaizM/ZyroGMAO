"use client";
import { useEffect, useMemo, useState } from "react";
import { 
  FaTools, 
  FaCheckCircle, 
  FaExclamationTriangle, 
  FaCog, 
  FaHeartbeat,
} from "react-icons/fa";
import { apiClient } from "../utils/api-client";
import { KpiService, type KpiSummary, type KpiTrends } from "../services/kpi.service";
import { InventoryService } from "../services/inventory.service";
import type { TaskUsedComponentRead } from "../types/inventory";
import { ManagementPageLayout } from "../components/layout/ManagementPageLayout";
import ProtectedPage from "../components/security/ProtectedPage";

// Removed WorkOrder mock; prioritizing daily spending KPI

type KpiCardProps = {
  icon: React.ReactNode;
  label: string;
  value: number;
  helpText: string;
  color: string;
  trend?: 'up' | 'down';
};

function KpiCard({ icon, label, value, helpText, color, trend }: KpiCardProps) {
  return (
    <div className="elegant-card p-6 border-l-4" 
         style={{ borderLeftColor: color }}>
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm font-medium text-muted">{label}</p>
          <p className="text-2xl font-bold mt-1 text-foreground" style={{ color }}>{value}</p>
          <div className="flex items-center mt-1">
            <p className="text-xs text-muted">{helpText}</p>
            {trend && (
              <span className={`ml-2 px-2 py-1 text-xs rounded-full ${
                trend === 'up' ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
              }`}>
                {trend === 'up' ? '↑' : '↓'} 12%
              </span>
            )}
          </div>
        </div>
        <div className="text-3xl opacity-80" style={{ color }}>
          {icon}
        </div>
      </div>
    </div>
  );
}


function TrendsChart({ trends }: { trends: KpiTrends | null }) {
  const [hover, setHover] = useState<{ idx: number; type: 'created' | 'completed'; value: number } | null>(null);
  if (!trends || trends.points.length === 0) return <div className="text-sm text-gray-500">No trend data yet.</div>;
  const maxVal = Math.max(1, ...trends.points.map(p => Math.max(p.created, p.completed)));
  const ticks = [0, 0.25, 0.5, 0.75, 1].map(f => Math.round(maxVal * f));
  return (
    <div className="w-full relative">
      <div className="flex h-40">
        {/* Eje Y */}
        <div className="flex flex-col justify-between mr-2 text-[10px] text-gray-500 py-1">
          {ticks.slice().reverse().map(t => <span key={t}>{t}</span>)}
        </div>
  <div className="flex items-end gap-2 flex-1 relative overflow-x-auto">
          {trends.points.map((p, idx) => {
            const createdH = (p.created / maxVal) * 100;
            const completedH = (p.completed / maxVal) * 100;
            return (
              <div key={idx} className="flex flex-col items-center w-12 shrink-0 relative">
                <div className="flex items-end gap-1 w-full h-32">
                  <div
                    className="bg-blue-400 w-4 rounded-sm relative cursor-pointer"
                    style={{ height: `${createdH}%` }}
                    onMouseEnter={() => setHover({ idx, type: 'created', value: p.created })}
                    onMouseLeave={() => setHover(h => h && h.idx === idx ? null : h)}
                  >
                    {hover && hover.idx === idx && hover.type === 'created' && (
                      <div className="absolute -top-5 left-1/2 -translate-x-1/2 text-[10px] bg-white/90 px-1 rounded shadow border">
                        {p.created}
                      </div>
                    )}
                  </div>
                  <div
                    className="bg-green-500 w-4 rounded-sm relative cursor-pointer"
                    style={{ height: `${completedH}%` }}
                    onMouseEnter={() => setHover({ idx, type: 'completed', value: p.completed })}
                    onMouseLeave={() => setHover(h => h && h.idx === idx ? null : h)}
                  >
                    {hover && hover.idx === idx && hover.type === 'completed' && (
                      <div className="absolute -top-5 left-1/2 -translate-x-1/2 text-[10px] bg-white/90 px-1 rounded shadow border">
                        {p.completed}
                      </div>
                    )}
                  </div>
                </div>
                <span className="mt-2 text-[10px] text-gray-500 text-center">{p.label}</span>
              </div>
            );
          })}
        </div>
      </div>
  <div className="flex justify-center gap-4 mt-3 text-xs">
        <div className="flex items-center gap-1 text-blue-600"><span className="inline-block w-3 h-3 bg-blue-400 rounded-sm"></span> Created</div>
        <div className="flex items-center gap-1 text-green-700"><span className="inline-block w-3 h-3 bg-green-500 rounded-sm"></span> Completed</div>
      </div>
    </div>
  );
}

function DailySpendChart({ data }: { data: { label: string; amount: number }[] }) {
  const [hover, setHover] = useState<number | null>(null);
  if (!data || data.length === 0) return <div className="text-sm text-gray-500">No spending data yet.</div>;
  const maxVal = Math.max(1, ...data.map(d => d.amount));
  const ticks = [0, 0.5, 1].map(f => +(maxVal * f).toFixed(0));
  return (
    <div className="w-full relative">
      <div className="flex h-40">
        <div className="flex flex-col justify-between mr-2 text-[10px] text-gray-500 py-1">
          {ticks.slice().reverse().map(t => <span key={t}>{t}</span>)}
        </div>
  <div className="h-full overflow-x-auto flex-1">
          <div className="h-full inline-flex items-end gap-2 pr-2">
            {data.map((d, idx) => {
              const h = (d.amount / maxVal) * 100;
              return (
                <div key={idx} className="flex flex-col items-center w-10 shrink-0 relative">
                  <div className="w-full h-32 flex items-end">
                    <div
                      className="w-6 mx-auto bg-purple-500 rounded-sm relative cursor-pointer"
                      style={{ height: `${h}%` }}
                      onMouseEnter={() => setHover(idx)}
                      onMouseLeave={() => setHover(hv => hv === idx ? null : hv)}
                    >
                      {hover === idx && (
                        <div className="absolute -top-5 left-1/2 -translate-x-1/2 text-[10px] bg-white/90 px-1 rounded shadow border whitespace-nowrap">
                          {d.amount.toFixed(2)}€
                        </div>
                      )}
                    </div>
                  </div>
                  <span className="mt-2 text-[10px] text-gray-500 text-center whitespace-nowrap">{d.label}</span>
                </div>
              );
            })}
          </div>
        </div>
      </div>
      <div className="flex justify-center gap-4 mt-3 text-xs text-purple-700">
        <div className="flex items-center gap-1"><span className="inline-block w-3 h-3 bg-purple-500 rounded-sm"></span> Daily spending (€)</div>
      </div>
    </div>
  );
}

function formatHours(h?: number | null) {
  if (h == null) return "-";
  if (h < 1) return `${Math.round(h * 60)} min`;
  const hrs = Math.floor(h);
  const mins = Math.round((h - hrs) * 60);
  return mins > 0 ? `${hrs}h ${mins}m` : `${hrs}h`;
}

function MonthlyResponseChart({ data }: { data: { month: string; avg_response_hours: number | null }[] }) {
  const [hoverIdx, setHoverIdx] = useState<number | null>(null);
  if (!data || data.length === 0) return <div className="text-sm text-gray-500">No data yet.</div>;
  const max = Math.max(1, ...data.map(d => d.avg_response_hours ?? 0));
  const ticks = [0, 0.5, 1].map(f => +(max * f).toFixed(0));
  return (
    <div className="w-full">
      <div className="flex h-40">
        <div className="flex flex-col justify-between mr-2 text-[10px] text-gray-500 py-1">
          {ticks.slice().reverse().map(t => <span key={t}>{t}</span>)}
        </div>
        <div className="flex items-end gap-3 flex-1 overflow-x-auto">
          <div className="inline-flex items-end gap-3 pr-2">
          {data.map((p, idx) => {
            const val = p.avg_response_hours ?? 0;
            const h = (val / max) * 100;
            return (
              <div key={p.month} className="flex flex-col items-center w-12 relative">
                <div className="w-full h-32 flex items-end">
                  <div
                    className="bg-blue-600 w-6 mx-auto rounded-sm relative cursor-pointer"
                    style={{ height: `${h}%` }}
                    onMouseEnter={() => setHoverIdx(idx)}
                    onMouseLeave={() => setHoverIdx(i => i === idx ? null : i)}
                  >
                    {hoverIdx === idx && (
                      <div className="absolute -top-5 left-1/2 -translate-x-1/2 text-[10px] bg-white/90 px-1 rounded shadow border whitespace-nowrap">
                        {val.toFixed(1)}h
                      </div>
                    )}
                  </div>
                </div>
                <span className="mt-2 text-[10px] text-gray-500">{p.month.slice(5)}</span>
              </div>
            );
          })}
          </div>
        </div>
      </div>
      <div className="mt-3 text-xs text-blue-700 flex items-center gap-1"><span className="inline-block w-3 h-3 bg-blue-600 rounded-sm"/> Average hours</div>
    </div>
  );
}

export default function Dashboard() {
  const [kpi, setKpi] = useState<KpiSummary | null>(null);
  const [trends, setTrends] = useState<KpiTrends | null>(null);
  const [dailySpend, setDailySpend] = useState<{ label: string; amount: number }[]>([]);
  const [monthlyResponse, setMonthlyResponse] = useState<{ month: string; avg_response_hours: number | null }[]>([]);

  const kpiService = useMemo(() => new KpiService(apiClient), []);
  const inventoryService = useMemo(() => new InventoryService(apiClient), []);

  useEffect(() => {
    let mounted = true;
    (async () => {
      try {
        const [summaryResp, trendsResp, usage, monthlyResp] = await Promise.all([
          kpiService.getSummary(),
          kpiService.getTrends(8),
          inventoryService.listUsage(),
          kpiService.getMonthlyResponse(6),
        ]);
        if (mounted) {
          setKpi(summaryResp);
          setTrends(trendsResp);
          setDailySpend(buildDailySpend(usage));
          setMonthlyResponse(monthlyResp.points);
        }
      } catch (e) {
        // Silent for now, show placeholders
        console.error('Error loading KPIs', e);
      }
    })();

    return () => { mounted = false; };
  }, [kpiService, inventoryService]);

  function buildDailySpend(usage: TaskUsedComponentRead[]): { label: string; amount: number }[] {
    // Group by day (last 30 days)
    const byDay = new Map<string, number>();
    const now = new Date();
    const start = new Date(now.getFullYear(), now.getMonth(), now.getDate());
    start.setDate(start.getDate() - 29);

    for (const u of usage) {
      const dt = new Date(u.created_at);
      // ignore outside window
      if (dt < start) continue;
      const dayKey = dt.toISOString().slice(0, 10); // YYYY-MM-DD
      const amount = (u.unit_cost_snapshot ?? 0) * u.quantity;
      byDay.set(dayKey, (byDay.get(dayKey) ?? 0) + amount);
    }

    // Build points for each day (filling gaps)
    const points: { label: string; amount: number }[] = [];
    for (let i = 0; i < 30; i++) {
      const d = new Date(start);
      d.setDate(start.getDate() + i);
      const key = d.toISOString().slice(0, 10);
      const label = `${d.getDate().toString().padStart(2, '0')}/${(d.getMonth() + 1).toString().padStart(2, '0')}`;
      points.push({ label, amount: +(byDay.get(key)?.toFixed(2) ?? 0) });
    }
    return points;
  }

  return (
    <ProtectedPage>
    <ManagementPageLayout>
      {/* KPIs Grid (dynamic) */}
  <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-5 gap-6 mb-8">
        <KpiCard
          icon={<FaExclamationTriangle />}
          label="Open orders"
          value={kpi?.open_workorders ?? 0}
          helpText={`Planned: ${kpi ? Math.round(kpi.planned_pct) : 0}%`}
          color="#F59E0B"
        />
        <KpiCard
          icon={<FaTools />}
          label="In progress"
          value={kpi?.in_progress_workorders ?? 0}
          helpText={`MTTR: ${formatHours(kpi?.mttr_hours)}`}
          color="#3B82F6"
        />
        <KpiCard
          icon={<FaCheckCircle />}
          label="Completed (30d)"
          value={kpi?.completed_workorders_30d ?? 0}
          helpText={`Avg completion time: ${formatHours(kpi?.avg_completion_time_hours)}`}
          color="#10B981"
        />
        <KpiCard
          icon={<FaCog />}
          label="Overdue"
          value={kpi?.overdue_workorders ?? 0}
          helpText={`MTBF: ${formatHours(kpi?.mtbf_hours)}`}
          color="#EF4444"
        />
        <KpiCard
          icon={<FaHeartbeat />}
          label="MTTF"
          value={kpi?.mttf_hours ? Math.round(kpi.mttf_hours) : 0}
          helpText={`MTTF: ${formatHours(kpi?.mttf_hours)}`}
          color="#8B5CF6"
        />
      </div>

      {/* Charts Grid: 50/50 width with same height and internal scroll */}
  <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
        {/* Card 1: Daily spending */}
        <div className="elegant-card p-6 h-[360px] flex flex-col overflow-hidden">
          <h3 className="text-lg font-semibold text-foreground mb-4">Daily component spending</h3>
          <div className="flex-1 min-h-0 overflow-auto">
            <DailySpendChart data={dailySpend} />
          </div>
        </div>
        {/* Card 2: Weekly trend */}
        <div className="elegant-card p-6 h-[360px] flex flex-col overflow-hidden">
          <h3 className="text-lg font-semibold text-foreground mb-4">Weekly trend</h3>
          <div className="flex-1 min-h-0 overflow-auto">
            <TrendsChart trends={trends} />
          </div>
        </div>
        {/* Card 3: Monthly response */}
        <div className="elegant-card p-6 h-[360px] flex flex-col overflow-hidden">
          <h3 className="text-lg font-semibold text-foreground mb-4">Monthly average response time</h3>
          <div className="flex-1 min-h-0 overflow-auto">
            {monthlyResponse.length === 0 ? (
              <div className="text-sm text-gray-500">No data yet.</div>
            ) : (
              <div className="w-full relative">
                <MonthlyResponseChart data={monthlyResponse} />
              </div>
            )}
          </div>
        </div>
      </div>
  </ManagementPageLayout>
  </ProtectedPage>
  );
}