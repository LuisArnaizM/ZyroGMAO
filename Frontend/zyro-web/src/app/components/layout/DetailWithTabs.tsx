"use client";

import React from 'react';
import { Button, Tabs, Typography } from 'antd';
import { ArrowLeftOutlined } from '@ant-design/icons';
import { useRouter } from 'next/navigation';

const { Title } = Typography;

export type TabDef = { key: string; tab: React.ReactNode; content: React.ReactNode };

interface DetailWithTabsProps {
  backHref?: string;
  onBack?: () => void;
  title: React.ReactNode;
  rightActions?: React.ReactNode;
  descriptions: React.ReactNode;
  tabs: TabDef[];
  defaultActiveKey?: string;
  extra?: React.ReactNode; // for additional modals or content
}

export default function DetailWithTabs({ backHref, onBack, title, rightActions, descriptions, tabs, defaultActiveKey = 'components', extra }: DetailWithTabsProps) {
  const router = useRouter();

  const handleBack = () => {
    if (onBack) return onBack();
    if (backHref) return router.push(backHref);
    return router.back();
  };

  return (
    <div className="gap-0.5 p-4" style={{ height: 'calc(100vh - 90px)' }}>
      <div style={{ marginBottom: 8, display: 'flex', alignItems: 'center', gap: 12 }}>
        <Button type="link" icon={<ArrowLeftOutlined />} onClick={handleBack} />
        <div style={{ flex: 1 }}>
          {typeof title === 'string' ? <Title level={4} style={{ margin: 0 }}>{title}</Title> : title}
        </div>
        {rightActions}
      </div>

      <div style={{ marginBottom: 12 }}>{descriptions}</div>

      <Tabs defaultActiveKey={defaultActiveKey}>
        {tabs.map(t => (
          <Tabs.TabPane tab={t.tab} key={t.key}>
            {t.content}
          </Tabs.TabPane>
        ))}
      </Tabs>

      {extra}
    </div>
  );
}
