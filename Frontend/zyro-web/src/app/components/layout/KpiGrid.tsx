"use client";
import React from 'react';
import { Card, Statistic } from 'antd';

type Kpi = {
  title: string;
  value: number | string;
  prefix?: React.ReactNode;
  valueStyle?: React.CSSProperties;
  color?: string; // color base para acento (hex o css var)
};

type KpiGridProps = {
  items: Kpi[];
  className?: string;
};

export function KpiGrid({ items, className }: KpiGridProps) {
  // Grid responsive por defecto: se adapta a la anchura disponible con columnas auto-fit
  const containerCls = className || 'grid grid-cols-[repeat(auto-fit,minmax(210px,1fr))] gap-4 mb-4';
  return (
    <div className={containerCls}>
      {items.map((kpi, idx) => {
        const accent = kpi.color || (kpi.valueStyle?.color as string) || '#3b82f6';
        const gradient = accent.startsWith('var(')
          ? undefined
          : `linear-gradient(90deg, ${accent}22, ${accent}08 40%, transparent)`; // transparencia hex 22 ~ 13%
        return (
          <Card
            key={idx}
            size="small"
            className="elegant-card kpi-card w-full min-w-0"
            style={{
              borderLeft: `4px solid ${accent}`,
              background: gradient,
            }}
          >
            <Statistic
              title={<span className="text-muted" style={{ fontSize: 12 }}>{kpi.title}</span>}
              value={kpi.value}
              prefix={kpi.prefix}
              valueStyle={{ color: 'var(--foreground)', fontWeight: 600, whiteSpace:'nowrap', ...kpi.valueStyle }}
            />
          </Card>
        );
      })}
    </div>
  );
}
