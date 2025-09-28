'use client';

import React, { useEffect, useState, useMemo, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import { Button, Space, Tag, Form, Input, Select, DatePicker, InputNumber, message } from 'antd';
import ModalDialog from '@/components/ui/ModalDialog';
import {
  HomeOutlined,
  CheckCircleOutlined,
  ExclamationCircleOutlined,
  ToolOutlined
} from '@ant-design/icons';
import type { ColumnsType } from 'antd/es/table';
import dayjs from 'dayjs';
import { useAuth } from '@/hooks/useAuth';
import { formatLabel, getAssetStatusColor } from '../utils/labels';
import { ManagementPageLayout } from '@/components/layout/ManagementPageLayout';
import { EntityList } from '@/components/data/EntityList';
import { AssetService } from '@/services/asset.service';
import { UserService } from '@/services/user.service';
import { AssetRead, AssetCreate, AssetUpdate, UserRead } from '@/types';
import { useAppDispatch, useAppSelector } from '@/store/hooks';
import { fetchAssetsKpi } from '@/store/slices/kpiSlice';

// const { Title } = Typography;
const { TextArea } = Input;
const { Option } = Select;

const ASSET_TYPES = [
  'Machinery',
  'Equipment',
  'Vehicle',
  'Tool',
  'Infrastructure',
  'IT Equipment',
  'Other'
];

const ASSET_STATUS = [
  { value: 'Active', color: 'green' },
  { value: 'Inactive', color: 'red' },
  { value: 'Maintenance', color: 'orange' },
  { value: 'Retired', color: 'gray' }
];

const AssetPage: React.FC = () => {
  const [assets, setAssets] = useState<AssetRead[]>([]);
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(20);
  const [total, setTotal] = useState<number | undefined>(undefined);
  // Selection handled in EntityList
  const [users, setUsers] = useState<UserRead[]>([]);
  const [loading, setLoading] = useState(false);
  const [modalVisible, setModalVisible] = useState(false);
  const [editingAsset, setEditingAsset] = useState<AssetRead | null>(null);
  // KPIs globales desde Redux
  const assetKpi = useAppSelector(s => s.kpi.assets);
  const dispatch = useAppDispatch();

  const [form] = Form.useForm();
  const router = useRouter();

  const { isAuthenticated, loading: authLoading } = useAuth();

  const assetService = useMemo(() => new AssetService(), []);
  const userService = useMemo(() => new UserService(), []);

  const fetchAssets = useCallback(async (p: number = page, ps: number = pageSize) => {
    try {
      setLoading(true);
      const data = await assetService.getAll({ page: p, page_size: ps });
      setAssets(data);
      // Calcular un total aproximado si el backend no lo proporciona
      const computedTotal = data.length === ps ? p * ps + 1 : (p - 1) * ps + data.length;
      setTotal(computedTotal);
    } catch (error) {
      console.error('Error loading assets:', error);
      message.error('Error loading assets');
    } finally {
      setLoading(false);
    }
  }, [assetService, page, pageSize]);

  const fetchUsers = useCallback(async () => {
    try {
      const data = await userService.getAll();
      setUsers(data);
    } catch (error) {
      console.error('Error loading users:', error);
      message.error('Error loading users');
    }
  }, [userService]);

  const loadData = useCallback(async () => {
    await Promise.all([fetchAssets(page, pageSize), fetchUsers()]);
  }, [fetchAssets, fetchUsers, page, pageSize]);

  const handleCreate = async (values: AssetCreate) => {
    try {
      const formattedValues = {
        ...values,
        purchase_date: values.purchase_date ? dayjs(values.purchase_date).format('YYYY-MM-DD') : undefined,
        warranty_expiry: values.warranty_expiry ? dayjs(values.warranty_expiry).format('YYYY-MM-DD') : undefined,
      };
      await assetService.create(formattedValues);
      message.success('Asset created successfully');
      setModalVisible(false);
      form.resetFields();
  fetchAssets();
  dispatch(fetchAssetsKpi());
    } catch (error) {
      console.error('Error creating asset:', error);
      message.error('Error creating asset');
    }
  };

  const handleUpdate = async (values: AssetUpdate) => {
    if (!editingAsset) return;
    try {
      const formattedValues = {
        ...values,
        purchase_date: values.purchase_date ? dayjs(values.purchase_date).format('YYYY-MM-DD') : undefined,
        warranty_expiry: values.warranty_expiry ? dayjs(values.warranty_expiry).format('YYYY-MM-DD') : undefined,
      };
      await assetService.update(editingAsset.id, formattedValues);
      message.success('Asset updated successfully');
      setModalVisible(false);
      setEditingAsset(null);
      form.resetFields();
      fetchAssets();
      dispatch(fetchAssetsKpi());
        } catch (error) {
      console.error('Error updating asset:', error);
      message.error('Error updating asset');
    }
  };

  const handleDelete = async (assetId: number) => {
    try {
      await assetService.delete(assetId);
      message.success('Asset deleted successfully');
  fetchAssets();
  dispatch(fetchAssetsKpi());
    } catch (error) {
      console.error('Error deleting asset:', error);
      message.error('Error deleting asset');
    }
  };

  const handleEdit = (asset: AssetRead) => {
    setEditingAsset(asset);
    form.setFieldsValue({
      ...asset,
      purchase_date: asset.purchase_date ? dayjs(asset.purchase_date) : undefined,
      warranty_expiry: asset.warranty_expiry ? dayjs(asset.warranty_expiry) : undefined,
    });
    setModalVisible(true);
  };

  const handleModalCancel = () => {
    setModalVisible(false);
    setEditingAsset(null);
    form.resetFields();
  };

  useEffect(() => {
    if (!authLoading && !isAuthenticated) {
      router.push('/login');
      return;
    }
    if (isAuthenticated) {
      loadData();
    }
  }, [isAuthenticated, authLoading, router, loadData]);

  const userMap = useMemo<Record<number, UserRead>>(() => {
    const map: Record<number, UserRead> = {};
    for (const u of users) map[u.id] = u;
    return map;
  }, [users]);

  const formatCurrency = useCallback((value?: number) => {
    if (value == null) return '-';
    try {
      return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(value);
    } catch {
      return `$${value}`;
    }
  }, []);

  const columns: ColumnsType<AssetRead> = [
    {
      title: 'ID',
      dataIndex: 'id',
      key: 'id',
      width: 80,
      sorter: (a, b) => a.id - b.id,
    },
    {
      title: 'Name',
      dataIndex: 'name',
      key: 'name',
      width: 220,
      ellipsis: true,
      sorter: (a, b) => a.name.localeCompare(b.name),
    },
    {
      title: 'Type',
      dataIndex: 'asset_type',
      key: 'asset_type',
      width: 150,
      filters: ASSET_TYPES.map(type => ({ text: type, value: type })),
      onFilter: (value, record) => record.asset_type === value,
    },
    {
      title: 'Model',
      dataIndex: 'model',
      key: 'model',
      width: 160,
      ellipsis: true,
    },
    {
      title: 'Serial Number',
      dataIndex: 'serial_number',
      key: 'serial_number',
      width: 200,
      ellipsis: true,
    },
    {
      title: 'Status',
      dataIndex: 'status',
      key: 'status',
      width: 140,
      filters: ASSET_STATUS.map(s => ({ text: s.value, value: s.value })),
      onFilter: (value, record) => record.status === value,
      render: (status: string) => <Tag color={getAssetStatusColor(status)}>{formatLabel(status)}</Tag>
    },
    {
      title: 'Responsible',
      dataIndex: 'responsible_id',
      key: 'responsible_id',
      width: 190,
      render: (id?: number) => {
        const u = id ? userMap[id] : undefined;
        return u ? `${u.first_name} ${u.last_name}` : '-';
      }
    },
    {
      title: 'Location',
      dataIndex: 'location',
      key: 'location',
      width: 160,
      ellipsis: true,
    },
    {
      title: 'Purchase Date',
      dataIndex: 'purchase_date',
      key: 'purchase_date',
      width: 140,
      render: (date?: string) => (date ? dayjs(date).format('YYYY-MM-DD') : '-')
    },
    {
      title: 'Purchase Cost',
      dataIndex: 'purchase_cost',
      key: 'purchase_cost',
      width: 140,
      align: 'right' as const,
      render: (v?: number) => formatCurrency(v)
    },
    {
      title: 'Current Value',
      dataIndex: 'current_value',
      key: 'current_value',
      width: 140,
      align: 'right' as const,
      render: (v?: number) => formatCurrency(v)
    },
    {
      title: 'Description',
      dataIndex: 'description',
      key: 'description',
      width: 260,
      ellipsis: true,
    }
  ];

  return (
    <>
      <ManagementPageLayout
        kpis={[
          { title: 'Total Assets', value: assetKpi?.total ?? 0, prefix: <HomeOutlined /> },
          { title: 'Active', value: assetKpi?.active ?? 0, prefix: <CheckCircleOutlined className="text-emerald-500" />, valueStyle: { color: '#22c55e' } },
          { title: 'In Maintenance', prefix: <ToolOutlined className="text-amber-500" />, value: assetKpi?.maintenance ?? 0, valueStyle: { color: '#f59e0b' } },
          { title: 'Inactive', value: assetKpi?.inactive ?? 0, prefix: <ExclamationCircleOutlined className="text-red-500" />, valueStyle: { color: '#ef4444' } },
          { title: 'Retired', value: assetKpi?.retired ?? 0, prefix: <ExclamationCircleOutlined className="text-neutral-400" />, valueStyle: { color: '#a3a3a3' } },
        ]}
        >
        <EntityList<AssetRead>
        title="Assets List"
        data={assets}
        columns={columns}
        rowKey="id"
        loading={loading}
        createLabel="Add New Asset"
        onCreate={() => setModalVisible(true)}
        onView={(row) => router.push(`/asset/${row.id}`)}
        onEdit={(row) => handleEdit(row)}
        onDelete={(row) => handleDelete(row.id)}
        pagination={{ current: page, pageSize, total }}
        onChangePage={(p, ps) => { setPage(p); setPageSize(ps); fetchAssets(p, ps); }}
  scrollX={1500}
        
      />

      {/* Create/Edit Modal */}
      <ModalDialog
        title={editingAsset ? 'Edit Asset' : 'Create New Asset'}
        open={modalVisible}
        onClose={handleModalCancel}
        width={600}
        primary={{ label: editingAsset ? 'Update' : 'Create', onClick: () => form.submit() }}
        secondary={{ label: 'Cancel', onClick: handleModalCancel }}
      >
        <Form form={form} layout="vertical" onFinish={editingAsset ? handleUpdate : handleCreate}>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <Form.Item
              name="name"
              label="Asset Name"
              rules={[{ required: true, message: 'Please enter asset name' }]}
            >
              <Input placeholder="Enter asset name" />
            </Form.Item>
            <Form.Item
              name="asset_type"
              label="Asset Type"
              rules={[{ required: true, message: 'Please select asset type' }]}
            >
              <Select placeholder="Select asset type">
                {ASSET_TYPES.map(type => (
                  <Option key={type} value={type}>{type}</Option>
                ))}
              </Select>
            </Form.Item>
          </div>

          <Form.Item name="description" label="Description">
            <TextArea rows={3} placeholder="Enter asset description" />
          </Form.Item>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <Form.Item name="model" label="Model">
              <Input placeholder="Enter model" />
            </Form.Item>
            <Form.Item name="serial_number" label="Serial Number">
              <Input placeholder="Enter serial number" />
            </Form.Item>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <Form.Item name="location" label="Location">
              <Input placeholder="Enter location" />
            </Form.Item>
            <Form.Item name="status" label="Status">
              <Select placeholder="Select status">
                {ASSET_STATUS.map(status => (
                  <Option key={status.value} value={status.value}>
                    {status.value}
                  </Option>
                ))}
              </Select>
            </Form.Item>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <Form.Item name="purchase_cost" label="Purchase Cost">
              <InputNumber
                className="w-full"
                placeholder="Enter purchase cost"
                formatter={(value) => `$ ${value}`.replace(/\B(?=(\d{3})+(?!\d))/g, ',')}
                parser={(value) => value!.replace(/\$\s?|(,*)/g, '')}
              />
            </Form.Item>
            <Form.Item name="current_value" label="Current Value">
              <InputNumber
                className="w-full"
                placeholder="Enter current value"
                formatter={(value) => `$ ${value}`.replace(/\B(?=(\d{3})+(?!\d))/g, ',')}
                parser={(value) => value!.replace(/\$\s?|(,*)/g, '')}
              />
            </Form.Item>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <Form.Item name="responsible_id" label="Responsible">
              <Select placeholder="Select responsible">
                {users.map((user) => (
                  <Option key={user.id} value={user.id}>
                    {user.first_name} {user.last_name}
                  </Option>
                ))}
              </Select>
            </Form.Item>
            <Form.Item name="purchase_date" label="Purchase Date">
              <DatePicker className="w-full" />
            </Form.Item>
            <Form.Item name="warranty_expiry" label="Warranty Expiry">
              <DatePicker className="w-full" />
            </Form.Item>
          </div>

          <Form.Item className="mb-0">
            <Space>
              <Button type="primary" htmlType="submit">
                {editingAsset ? 'Update' : 'Create'}
              </Button>
              <Button onClick={handleModalCancel}>Cancel</Button>
            </Space>
          </Form.Item>
        </Form>
      </ModalDialog>
    </ManagementPageLayout>
    </>
  );
};

export default AssetPage;