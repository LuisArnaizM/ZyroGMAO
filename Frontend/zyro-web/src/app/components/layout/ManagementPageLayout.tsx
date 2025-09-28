"use client";
import React from 'react';
import { KpiGrid } from './KpiGrid';

type Kpi = {
  title: string;
  value: number | string;
  prefix?: React.ReactNode;
  valueStyle?: React.CSSProperties;
};

// eslint-disable-next-line @typescript-eslint/no-unused-vars
type ManagementPageLayoutProps<T extends object = Record<string, unknown>> = {
  kpis?: Kpi[];
  kpiClassName?: string;
  className?: string;
  children: React.ReactNode;
  headerActions?: React.ReactNode;

};
export function ManagementPageLayout<T extends object = Record<string, unknown>>({ kpis, kpiClassName, className, children, headerActions }: ManagementPageLayoutProps<T>) {
  return (
    <div
      className={(className ? className + ' ' : '') + 'mgmt-layout flex flex-col p-4'}
    >
      {(kpis && kpis.length > 0) || headerActions ? (
        <div className="flex items-start gap-4 mb-2 min-w-0">
          {kpis && kpis.length > 0 && <div className="flex-1 min-w-0"><KpiGrid items={kpis} className={kpiClassName} /></div>}
          {headerActions && (
            <div className="shrink-0 flex flex-col items-end gap-2">{headerActions}</div>
          )}
        </div>
      ) : null}
  <div className="flex-1 min-h-0 flex flex-col">
        {children}
      </div>
    </div>
  );
}