"use client";
import React from 'react';
import { Card, Typography } from 'antd';

const { Title } = Typography;

type ListCardProps = {
  icon?: React.ReactNode;
  title: string;
  action?: React.ReactNode;
  actions?: React.ReactNode;
  children: React.ReactNode;
  className?: string;
};

export function ListCard({ title, action, actions, children, className }: ListCardProps) {
  return (
    <Card
      className={`elegant-card ${className || 'flex-1 min-h-0 overflow-hidden flex flex-col'}`}
    >
      <div className="flex items-center justify-between mb-2">
        <Title level={4} className="!m-0">{title}</Title>
        <div className="flex justify-end items-center gap-2">
          {action}
          {actions}
        </div>
      </div>
      <div className="flex-1 min-h-0">
        {children}
      </div>
    </Card>
  );
}
