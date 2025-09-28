"use client";

import React, { useEffect, useMemo, useState } from 'react';
import { Button, Col, Form, InputNumber, Row, Select, Tag, message, Table, Descriptions } from 'antd';
import ModalDialog from '../components/ui/ModalDialog';
import type { ColumnsType } from 'antd/es/table';
import { apiClient } from '../utils/api-client';
import { InventoryService } from '../services/inventory.service';
import type { InventoryItemReadWithComponent, TaskUsedComponentRead } from '../types/inventory';
import type { ComponentRead, ComponentDetail } from '../types';
import { ManagementPageLayout } from '../components/layout/ManagementPageLayout';
import { ComponentService } from '../services/component.service';
import { EntityList } from '../components/data/EntityList';

const { Option } = Select;

export default function InventoryPage() {
  const inventoryService = useMemo(() => new InventoryService(apiClient), []);
  const componentService = useMemo(() => new ComponentService(), []);

  const [loading, setLoading] = useState(false);
  const [components, setComponents] = useState<ComponentRead[]>([]);
  const [items, setItems] = useState<InventoryItemReadWithComponent[]>([]);
  // Paginación controlada (client-side)
  const [pageCurrent, setPageCurrent] = useState(1);
  const [pageSize, setPageSize] = useState(10);
  const [typeFilter, setTypeFilter] = useState<string | undefined>(undefined);

  const [adjustModalOpen, setAdjustModalOpen] = useState(false);
  const [adjustTarget, setAdjustTarget] = useState<InventoryItemReadWithComponent | null>(null);
  const [adjustDelta, setAdjustDelta] = useState<number>(0);

  const [createModalOpen, setCreateModalOpen] = useState(false);
  const [createForm] = Form.useForm<{ component_id: number; quantity: number; unit_cost?: number }>();

  // Modal de detalles (doble click)
  const [detailOpen, setDetailOpen] = useState(false);
  const [detailLoading, setDetailLoading] = useState(false);
  const [detailItem, setDetailItem] = useState<InventoryItemReadWithComponent | null>(null);
  const [detailComponent, setDetailComponent] = useState<ComponentDetail | null>(null);
  const [detailUsage, setDetailUsage] = useState<TaskUsedComponentRead[]>([]);

  const loadAll = async (type?: string) => {
    setLoading(true);
    try {
  const inv = await inventoryService.list(type);
  setItems(inv || []);
    } catch (e) {
      console.error(e);
      message.error('Error loading inventory');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { loadAll(typeFilter); // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [typeFilter]);

  // Resetear página si cambian los filtros o el tamaño de la lista hace que la página actual quede fuera de rango
  useEffect(() => {
    const totalPages = Math.max(1, Math.ceil(items.length / pageSize));
    if (pageCurrent > totalPages) setPageCurrent(1);
  }, [items, pageSize, pageCurrent]);

  // Cargar componentes para el modal de creación (se usa para ofrecer componentes sin ítem de inventario)
  useEffect(() => {
    const run = async () => {
      try {
        const all = await componentService.getAll();
        setComponents(all || []);
      } catch (e) {
        console.error('Error loading components for inventory create', e);
      }
    };
    run();
  }, [componentService]);

  const allTypes = useMemo(() => Array.from(new Set((items || []).map(i => i.component?.component_type).filter(Boolean))).sort() as string[], [items]);

  const columns: ColumnsType<InventoryItemReadWithComponent> = [
    {
      title: 'Component',
      dataIndex: ['component','name'],
      key: 'component',
      render: (_: unknown, r) => r.component ? r.component.name : '-'
    },
    {
      title: 'Type',
      key: 'type',
      render: (_, r) => r.component ? <Tag>{r.component.component_type}</Tag> : '-'
    },
    {
      title: 'Asset',
      key: 'asset',
      render: (_, r) => r.component ? `#${r.component.asset_id}` : '-'
    },
    {
      title: 'Quantity',
      dataIndex: 'quantity',
      key: 'quantity',
    },
    {
      title: 'Unit Cost',
      dataIndex: 'unit_cost',
      key: 'unit_cost',
      render: (v?: number) => v != null ? `$${v.toFixed(2)}` : '-'
    },
  ];

  const openDetails = async (record: InventoryItemReadWithComponent) => {
    setDetailOpen(true);
    setDetailLoading(true);
    setDetailItem(record);
    try {
      const [comp, usage] = await Promise.all([
        componentService.getById(record.component.id),
        inventoryService.listUsage(record.component.id),
      ]);
      setDetailComponent(comp || null);
      // ordenar últimos movimientos por fecha desc
      const sorted = [...(usage || [])].sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime());
      setDetailUsage(sorted);
    } catch (e) {
      console.error('Error loading details', e);
      message.error('No se pudieron cargar los detalles');
      setDetailComponent(null);
      setDetailUsage([]);
    } finally {
      setDetailLoading(false);
    }
  };

  const openCreate = () => {
    createForm.resetFields();
    setCreateModalOpen(true);
  };


  const handleAdjust = async () => {
    if (!adjustTarget) return;
    try {
      await inventoryService.adjust(adjustTarget.id, adjustDelta);
      message.success('Stock adjusted');
      setAdjustModalOpen(false);
      await loadAll(typeFilter);
    } catch (e: unknown) {
      const err = e as { message?: string };
      if (err?.message) message.error(err.message);
    }
  };

  const componentsWithoutInventory = useMemo(() => {
    const withInvIds = new Set((items || []).map(i => i.component?.id).filter(Boolean) as number[]);
    return components.filter(c => !withInvIds.has(c.id));
  }, [components, items]);

  return (
    <ManagementPageLayout>
      <EntityList<InventoryItemReadWithComponent>
        title="Inventory Items"
        data={items}
        columns={columns}
        rowKey="id"
        loading={loading}
        createLabel="Add Item"
        onCreate={openCreate}
        onView={(record) => openDetails(record)}
        pagination={{ current: pageCurrent, pageSize, total: items.length }}
        onChangePage={(p, ps) => { setPageCurrent(p); setPageSize(ps); }}
        headerExtras={(selected) => (
          <div className="flex items-center gap-2">
            <Select
              allowClear
              placeholder="Filter by type"
              style={{ width: 220 }}
              value={typeFilter}
              onChange={v => setTypeFilter(v)}
            >
              {allTypes.map(t => <Option key={t} value={t}>{t}</Option>)}
            </Select>
            <Button
              disabled={!selected}
              onClick={() => {
                if (selected) {
                  setAdjustTarget(selected as InventoryItemReadWithComponent);
                  setAdjustDelta(0);
                  setAdjustModalOpen(true);
                }
              }}
            >
              Adjust stock
            </Button>
          </div>
        )}
        scrollY={'calc(100vh - 300px)'}
      />

      <ModalDialog open={createModalOpen} title="Add Inventory Item" onClose={() => setCreateModalOpen(false)} primary={{ label: 'Create', onClick: () => createForm.submit() }} secondary={{ label: 'Cancel', onClick: () => setCreateModalOpen(false) }}>
            <Form form={createForm} layout="vertical">
          <Form.Item name="component_id" label="Component" rules={[{ required: true }]}> 
            <Select showSearch placeholder="Select component">
              {componentsWithoutInventory.map(c => (
                <Option key={c.id} value={c.id}>{c.name} ({c.component_type})</Option>
              ))}
            </Select>
          </Form.Item>
          <Form.Item name="quantity" label="Quantity" rules={[{ required: true }]}>
            <InputNumber min={0} style={{ width: '100%' }} />
          </Form.Item>
          <Form.Item name="unit_cost" label="Unit Cost">
            <InputNumber min={0} step={0.01} style={{ width: '100%' }} />
          </Form.Item>
            </Form>
          </ModalDialog>

      <ModalDialog open={adjustModalOpen} title={`Adjust Stock for #${adjustTarget?.id}`} onClose={() => setAdjustModalOpen(false)} primary={{ label: 'Apply', onClick: () => handleAdjust() }} secondary={{ label: 'Cancel', onClick: () => setAdjustModalOpen(false) }}>
        <Row gutter={12}>
          <Col span={24}>
            <p>Use negative values to subtract stock.</p>
            <InputNumber value={adjustDelta} onChange={v => setAdjustDelta(Number(v))} step={0.5} style={{ width: '100%' }} />
          </Col>
        </Row>
      </ModalDialog>

      <ModalDialog
        open={detailOpen}
        title={detailItem ? `Component #${detailItem.component.id} - ${detailItem.component.name}` : 'Details'}
        onClose={() => setDetailOpen(false)}
        width={760}
        secondary={{ label: 'Close', onClick: () => setDetailOpen(false) }}
      >
        {detailLoading ? (
          <div>Loading...</div>
        ) : detailItem && (
          <div className="space-y-4">
            <Descriptions bordered size="small" column={2}>
              <Descriptions.Item label="Component">{detailItem.component.name}</Descriptions.Item>
              <Descriptions.Item label="Type">{detailItem.component.component_type}</Descriptions.Item>
              <Descriptions.Item label="Model">{detailComponent?.model || '-'}</Descriptions.Item>
              <Descriptions.Item label="Serial">{detailComponent?.serial_number || '-'}</Descriptions.Item>
              <Descriptions.Item label="Status">{detailComponent?.status || '-'}</Descriptions.Item>
              <Descriptions.Item label="Asset">#{detailItem.component.asset_id}</Descriptions.Item>
              <Descriptions.Item label="Stock">{detailItem.quantity}</Descriptions.Item>
              <Descriptions.Item label="Unit Cost">{detailItem.unit_cost != null ? `$${detailItem.unit_cost.toFixed(2)}` : '-'}</Descriptions.Item>
            </Descriptions>

            <div>
              <h4 className="mb-2">Últimos movimientos (uso en tareas)</h4>
              <Table<TaskUsedComponentRead>
                size="small"
                rowKey="id"
                dataSource={detailUsage}
                pagination={{ pageSize: 5 }}
                columns={[
                  { title: 'Fecha', dataIndex: 'created_at', key: 'created_at', render: (v: string) => new Date(v).toLocaleString() },
                  { title: 'Task', dataIndex: 'task_id', key: 'task_id', render: (v: number) => `#${v}` },
                  { title: 'Qty', dataIndex: 'quantity', key: 'quantity' },
                  { title: 'Unit Cost', dataIndex: 'unit_cost_snapshot', key: 'unit_cost_snapshot', render: (v?: number) => v != null ? `$${v.toFixed(2)}` : '-' },
                ]}
              />
            </div>
          </div>
        )}
  </ModalDialog>
    </ManagementPageLayout>
  );
}
