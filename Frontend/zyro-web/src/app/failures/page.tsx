'use client';

import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { Tag, Form, Input, Select, DatePicker, message, Tooltip } from 'antd';
import { CheckCircleOutlined, ExclamationCircleOutlined, AlertOutlined, PlusOutlined, EyeOutlined } from '@ant-design/icons';
import type { ColumnsType } from 'antd/es/table';
import dayjs from 'dayjs';

import { ManagementPageLayout } from '../components/layout/ManagementPageLayout';
import { EntityList } from '../components/data/EntityList';
import WorkOrderModal from '../components/workorders/WorkOrderModal';
import ModalDialog from '../components/ui/ModalDialog';
import { useAuth } from '../hooks/useAuth';
import { useRouter } from 'next/navigation';
import { FailureService } from '../services/failure.service';
import { WorkOrderCreate } from '../types/workorder';
import { AssetService } from '../services/asset.service';
import { AssetRead, FailureCreate, FailureRead, FailureUpdate, FailureWithWorkOrder } from '../types';
import { useAppDispatch, useAppSelector } from '../store/hooks';
import { fetchFailuresKpi } from '../store/slices/kpiSlice';

const { TextArea } = Input;
const { Option } = Select;

import { formatLabel, getSeverityColor, getFailureStatusColor } from '../utils/labels';

const SEVERITY_OPTIONS: { value: string; color: string; label: string }[] = [
  { value: 'low', label: 'Low', color: 'green' },
  { value: 'medium', label: 'Medium', color: 'orange' },
  { value: 'high', label: 'High', color: 'red' },
  { value: 'critical', label: 'Critical', color: 'magenta' },
];

// Estados conocidos según uso en servicios (pending / resolved) y uno intermedio
const FAILURE_STATUS = [
  { value: 'pending', label: 'Pending', color: 'orange' },
  { value: 'in_progress', label: 'In Progress', color: 'blue' },
  { value: 'resolved', label: 'Resolved', color: 'green' },
];

const FailuresPage: React.FC = () => {
  const [failures, setFailures] = useState<FailureWithWorkOrder[]>([]);
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(20);
  const [total, setTotal] = useState<number | undefined>(undefined);
  const [assets, setAssets] = useState<AssetRead[]>([]);
  const [loading, setLoading] = useState(false);
  const [modalVisible, setModalVisible] = useState(false);
  const [editingFailure, setEditingFailure] = useState<FailureRead | null>(null);
  const [woModalOpen, setWoModalOpen] = useState(false);
  const [woPrefill, setWoPrefill] = useState<Partial<WorkOrderCreate> | undefined>(undefined);
  // KPIs globales desde Redux
  const failureKpi = useAppSelector(s => s.kpi.failures);

  const [form] = Form.useForm();
  const router = useRouter();
  const { isAuthenticated, loading: authLoading } = useAuth();

  const failureService = useMemo(() => new FailureService(), []);
  const assetService = useMemo(() => new AssetService(), []);
  const dispatch = useAppDispatch();

  const fetchFailuresWithWorkOrders = useCallback(async () => {
    setLoading(true);
    try {
      const [fRes, aRes] = await Promise.allSettled([
        failureService.getFailuresWithWorkOrders(),
        assetService.getAll({ page: 1, page_size: 1000 }),
      ]);

      if (fRes.status === 'fulfilled') {
        const failures = fRes.value;
        setFailures(failures);
        setTotal(failures.length);
      } else {
        console.warn('Failed to load failures:', fRes.reason);
        message.warning('No se pudo cargar la lista de fallos');
      }

      if (aRes.status === 'fulfilled') {
        const a = aRes.value;
        setAssets(Array.isArray(a) ? a : []);
      } else {
        console.warn('Failed to load assets:', aRes.reason);
        message.warning('No se pudo cargar la lista de activos');
      }

      // Actualizar KPIs
      dispatch(fetchFailuresKpi());
    } catch (error) {
      console.error('Error fetching failures:', error);
      message.error('Error cargando los datos');
    } finally {
      setLoading(false);
    }
  }, [failureService, assetService, dispatch]);

  useEffect(() => {
    if (!authLoading && !isAuthenticated) {
      router.push('/login');
      return;
    }
    if (isAuthenticated) {
      fetchFailuresWithWorkOrders();
    }
  }, [isAuthenticated, authLoading, router, fetchFailuresWithWorkOrders]);

  const assetMap = useMemo(() => {
    const map: Record<number, AssetRead> = {};
    for (const a of assets) map[a.id] = a;
    return map;
  }, [assets]);

  const handleOpenCreate = async () => {
    setEditingFailure(null);
    form.resetFields();
    // Asegurar que los activos estén disponibles para el selector
    if (!assets || assets.length === 0) {
      try {
        const a = await assetService.getAll();
        setAssets(Array.isArray(a) ? a : []);
      } catch (e) {
        console.warn('Failed to load assets on open:', e);
        message.error('No se pudieron cargar los activos');
      }
    }
    setModalVisible(true);
  };

  const handleEdit = (failure: FailureRead) => {
    setEditingFailure(failure);
    form.setFieldsValue({
      description: failure.description,
      asset_id: failure.asset_id,
      severity: failure.severity,
      status: failure.status,
      resolved_date: failure.resolved_date ? dayjs(failure.resolved_date) : undefined,
      resolution_notes: failure.resolution_notes,
    });
    setModalVisible(true);
  };

  const handleDelete = async (id: number) => {
    try {
      await failureService.delete(id);
      message.success('Failure deleted successfully');
      await fetchFailuresWithWorkOrders();
  dispatch(fetchFailuresKpi());
    } catch (e) {
      console.error('Delete failure error:', e);
      message.error('Error deleting failure');
    }
  };

  const handleSubmit = async (values: Partial<FailureCreate & FailureUpdate>) => {
    try {
      if (editingFailure) {
        const payload: FailureUpdate = {
          description: values.description,
          status: values.status,
          severity: values.severity as string | undefined,
          resolved_date: values.resolved_date ? dayjs(values.resolved_date as unknown as dayjs.Dayjs).toISOString() : undefined,
          resolution_notes: values.resolution_notes,
        };
        await failureService.update(editingFailure.id, payload);
        message.success('Failure updated successfully');
      } else {
        const payload: FailureCreate = {
          description: values.description!,
          asset_id: values.asset_id,
          severity: values.severity as string | undefined,
        };
        if (!payload.asset_id) {
          message.error('Please select an asset');
          return;
        }
        await failureService.create(payload);
        message.success('Failure created successfully');
      }
      setModalVisible(false);
      form.resetFields();
      await fetchFailuresWithWorkOrders();
  dispatch(fetchFailuresKpi());
    } catch (e) {
      console.error('Save failure error:', e);
      message.error('Error saving failure');
    }
  };

  const handleCreateWorkOrder = (failure: FailureWithWorkOrder) => {
    // Asegurarse de que el prefill incluye failure_id
    const pre: Partial<WorkOrderCreate> = {
      title: `Repair: ${failure.description ? failure.description.slice(0, 80) : 'Failure'}`,
      description: failure.description,
      asset_id: failure.asset_id,
      failure_id: failure.id, // Este campo se pasa explícitamente
    };
    setWoPrefill(pre);
    setWoModalOpen(true);
  };

  const handleViewWorkOrder = (workorderId: number) => {
    router.push(`/workorders/${workorderId}`);
  };

  const columns: ColumnsType<FailureWithWorkOrder> = [
    { title: 'ID', dataIndex: 'id', key: 'id', width: 80, sorter: (a, b) => a.id - b.id },
    { title: 'Description', dataIndex: 'description', key: 'description', ellipsis: true },
    {
      title: 'Asset',
      dataIndex: 'asset_id',
      key: 'asset_id',
  render: (assetId?: number) => (assetId ? (assetMap[assetId]?.name || `#${assetId}`) : '-'),
      filters: assets.map(a => ({ text: a.name, value: a.id })),
      onFilter: (value, record) => record.asset_id === value,
    },
    {
      title: 'Severity',
      dataIndex: 'severity',
      key: 'severity',
      render: (sev: string) => {
        const cfg = SEVERITY_OPTIONS.find(s => s.value === sev);
        const value = cfg?.value || sev;
        const label = cfg?.label || sev;
        return <Tag color={getSeverityColor(value)}>{formatLabel(label)}</Tag>;
      },
      filters: SEVERITY_OPTIONS.map(s => ({ text: s.label, value: s.value })),
      onFilter: (value, record) => record.severity === value,
    },
    {
      title: 'Status',
      dataIndex: 'status',
      key: 'status',
      render: (status: string) => {
        const cfg = FAILURE_STATUS.find(s => s.value === status);
        const label = cfg?.label || status;
        return <Tag color={getFailureStatusColor(status)}>{formatLabel(label)}</Tag>;
      },
      filters: FAILURE_STATUS.map(s => ({ text: s.label, value: s.value })),
      onFilter: (value, record) => record.status === value,
    },
    {
      title: 'Reported Date',
      dataIndex: 'reported_date',
      key: 'reported_date',
      render: (date?: string) => (date ? dayjs(date).format('YYYY-MM-DD HH:mm') : '-'),
      sorter: (a, b) => dayjs(a.reported_date).unix() - dayjs(b.reported_date).unix(),
    },
    {
      title: 'Resolved Date',
      dataIndex: 'resolved_date',
      key: 'resolved_date',
      render: (date?: string) => (date ? dayjs(date).format('YYYY-MM-DD HH:mm') : '-'),
      sorter: (a, b) => {
        const da = a.resolved_date ? dayjs(a.resolved_date).unix() : 0;
        const db = b.resolved_date ? dayjs(b.resolved_date).unix() : 0;
        return da - db;
      },
    },
    {
      title: 'Work Order',
      key: 'workorder',
      width: 120,
      render: (_, record: FailureWithWorkOrder) => {
        if (record.workorder_id) {
          // Si hay workorder_id, mostrar botón para ver
          return (
            <Tooltip title={`View Work Order #${record.workorder_id}`}>
              <button
                className="btn btn--primary btn--sm"
                onClick={() => handleViewWorkOrder(record.workorder_id!)}
              >
                <EyeOutlined />
                #{record.workorder_id}
              </button>
            </Tooltip>
          );
        } else {
          // Si no hay workorder, mostrar botón para crear
          return (
            <Tooltip title="Create Work Order">
              <button
                className="btn btn--secondary btn--sm"
                onClick={() => handleCreateWorkOrder(record)}
              >
                <PlusOutlined />
                Create
              </button>
            </Tooltip>
          );
        }
      },
    },
  ];

  return (
    <ManagementPageLayout
      kpis={[
        { title: 'Total Failures', value: failureKpi?.total ?? 0, prefix: <ExclamationCircleOutlined /> },
        { title: 'Pending', value: failureKpi?.pending ?? 0, prefix: <AlertOutlined style={{ color: '#faad14' }} />, valueStyle: { color: '#faad14' } },
        { title: 'Resolved', value: failureKpi?.resolved ?? 0, prefix: <CheckCircleOutlined style={{ color: '#52c41a' }} />, valueStyle: { color: '#52c41a' } },
        { title: 'Critical', value: failureKpi?.critical ?? 0, prefix: <ExclamationCircleOutlined style={{ color: '#f5222d' }} />, valueStyle: { color: '#f5222d' } },
      ]}
    >
        <EntityList<FailureWithWorkOrder>
          title="Failures List"
          data={failures}
          columns={columns}
          rowKey="id"
          loading={loading}
          createLabel="Report Failure"
          onCreate={handleOpenCreate}
          onView={(row) => handleEdit(row)}
          onDoubleClick={(row) => {
            if (row.workorder_id) {
              // Si ya tiene workorder asociada, navegar a la página de la workorder
              handleViewWorkOrder(row.workorder_id);
            } else {
              // Si no tiene workorder, pre-llenar el modal para crear una nueva
              const pre = {
                title: `Repair: ${row.description ? row.description.slice(0, 80) : 'Failure'}`,
                description: row.description,
                asset_id: row.asset_id,
                failure_id: row.id,
              };
              setWoPrefill(pre);
              setWoModalOpen(true);
            }
          }}
          onEdit={(row) => handleEdit(row)}
          onDelete={(row) => handleDelete(row.id)}
          pagination={{ current: page, pageSize, total }}
          onChangePage={(p, ps) => { setPage(p); setPageSize(ps); setTimeout(() => fetchFailuresWithWorkOrders(), 0); }}
          scrollX={1000}
        />
      

      <ModalDialog
        open={modalVisible}
        title={editingFailure ? 'Edit Failure' : 'Report New Failure'}
        onClose={() => { setModalVisible(false); setEditingFailure(null); form.resetFields(); }}
        width={720}
        primary={{ label: editingFailure ? 'Update' : 'Create', onClick: () => form.submit() }}
        secondary={{ label: 'Cancel', onClick: () => { setModalVisible(false); setEditingFailure(null); form.resetFields(); } }}
      >
        <Form
          form={form}
          layout="vertical"
          onFinish={handleSubmit}
          initialValues={{}}
        >
          <Form.Item name="description" label="Description" rules={[{ required: true, message: 'Please enter a description' }]}> 
            <TextArea rows={3} placeholder="Describe the failure" />
          </Form.Item>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <Form.Item name="asset_id" label="Asset" rules={[{ required: !editingFailure, message: 'Please select an asset' }]}> 
              <Select placeholder="Select asset">
                {assets.map(a => (
                  <Option key={a.id} value={a.id}>{a.name}</Option>
                ))}
              </Select>
            </Form.Item>
            <Form.Item name="severity" label="Severity">
              <Select allowClear placeholder="Select severity">
                {SEVERITY_OPTIONS.map(s => (
                  <Option key={s.value} value={s.value}>{s.label}</Option>
                ))}
              </Select>
            </Form.Item>
            {editingFailure && (
              <Form.Item name="status" label="Status">
                <Select placeholder="Select status">
                  {FAILURE_STATUS.map(s => (
                    <Option key={s.value} value={s.value}>{s.label}</Option>
                  ))}
                </Select>
              </Form.Item>
            )}
          </div>

          {editingFailure && (
            <>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <Form.Item name="resolved_date" label="Resolved Date">
                  <DatePicker className="w-full" showTime />
                </Form.Item>
                <Form.Item name="resolution_notes" label="Resolution Notes">
                  <Input placeholder="Optional" />
                </Form.Item>
              </div>
            </>
          )}

        </Form>
      </ModalDialog>
      <WorkOrderModal
        open={woModalOpen}
        onClose={() => { setWoModalOpen(false); setWoPrefill(undefined); }}
        onCreated={async () => { 
          // Refrescar failures para obtener los workorder_id actualizados
          await fetchFailuresWithWorkOrders();
          // Luego actualizar KPIs
          dispatch(fetchFailuresKpi()); 
        }}
        prefill={woPrefill}
        assets={assets}
      />
  </ManagementPageLayout>
  );
};

export default FailuresPage;
