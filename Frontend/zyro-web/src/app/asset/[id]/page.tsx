'use client';

import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import {
  Col,
  Descriptions,
  Form,
  Input,
  Select,
  DatePicker,
  InputNumber,
  Row,
  Spin,
  Tag,
  message,
} from 'antd';
import dayjs from 'dayjs';
import { useAuth } from '../../hooks/useAuth';
import { AssetService } from '../../services/asset.service';
import { ComponentService } from '../../services/component.service';
import { MaintenanceService } from '../../services/maintenance.service';
import { MaintenancePlanService } from '../../services/maintenancePlan.service';
import { EntityList } from '../../components/data/EntityList';
import type { AssetRead, ComponentRead, ComponentCreate, ComponentUpdate, MaintenanceRead, MaintenanceCreate, MaintenanceUpdate } from '../../types';
import { UserService } from '../../services/user.service';
import { formatLabel, getMaintenanceStatusColor, getComponentStatusColor } from '../../utils/labels';
import type { ColumnsType } from 'antd/es/table';
// AppButton removed - not used in this view
import ModalDialog from '../../components/ui/ModalDialog';
import DetailWithTabs, { TabDef } from '../../components/layout/DetailWithTabs';

// Asset status constants moved to utils/labels

export default function AssetDetailPage() {
  const params = useParams();
  const router = useRouter();
  const { isAuthenticated, loading: authLoading } = useAuth();

  const assetId = useMemo(() => {
    const raw = params?.id as string | string[] | undefined;
    const idStr = Array.isArray(raw) ? raw[0] : raw;
    return idStr ? Number(idStr) : NaN;
  }, [params]);

  const assetService = useMemo(() => new AssetService(), []);
  const componentService = useMemo(() => new ComponentService(), []);
  const maintenanceService = useMemo(() => new MaintenanceService(), []);
  const maintenancePlanService = useMemo(() => new MaintenancePlanService(), []);
  const userService = useMemo(() => new UserService(), []);

  // Local types for frontend usage
  type UserRead = { id: number; first_name?: string; last_name?: string; };
  // Ajuste: reflejar los campos reales devueltos por la API de maintenance plans
  type MaintenancePlanRead = {
    id: number;
    name: string;
    description?: string | null;
    plan_type?: string | null; // PREVENTIVE / INSPECTION / PREDICTIVE
    frequency_days?: number | null;
    frequency_weeks?: number | null;
    frequency_months?: number | null;
    estimated_duration?: number | null;
    estimated_cost?: number | null;
    start_date?: string;
    next_due_date?: string | null;
    last_execution_date?: string | null;
    active?: boolean | null;
    asset_id?: number | null;
    component_id?: number | null;
    created_at?: string;
    updated_at?: string | null;
  };

  const [loading, setLoading] = useState(false);
  const [asset, setAsset] = useState<AssetRead | null>(null);
  const [components, setComponents] = useState<ComponentRead[]>([]);
  const [maintenances, setMaintenances] = useState<MaintenanceRead[]>([]);
  const [maintenancePlans, setMaintenancePlans] = useState<MaintenancePlanRead[]>([]);
  const [users, setUsers] = useState<UserRead[]>([]);

  // Estados de paginación para cada EntityList
  const [componentsPage, setComponentsPage] = useState(1);
  const [componentsPageSize, setComponentsPageSize] = useState(10);
  const [maintenancesPage, setMaintenancesPage] = useState(1);
  const [maintenancesPageSize, setMaintenancesPageSize] = useState(10);
  const [maintenancePlansPage, setMaintenancePlansPage] = useState(1);
  const [maintenancePlansPageSize, setMaintenancePlansPageSize] = useState(10);

  // Handlers para cambios de página
  const handleComponentsPageChange = (page: number, pageSize: number) => {
    setComponentsPage(page);
    setComponentsPageSize(pageSize);
  };

  const handleMaintenancesPageChange = (page: number, pageSize: number) => {
    setMaintenancesPage(page);
    setMaintenancesPageSize(pageSize);
  };

  const handleMaintenancePlansPageChange = (page: number, pageSize: number) => {
    setMaintenancePlansPage(page);
    setMaintenancePlansPageSize(pageSize);
  };

  // Maintenance Plan modals/forms
  const [maintenancePlanModalVisible, setMaintenancePlanModalVisible] = useState(false);
  const [editingMaintenancePlan, setEditingMaintenancePlan] = useState<MaintenancePlanRead | null>(null);
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  type MaintenancePlanFormValues = any;
  const [maintenancePlanForm] = Form.useForm<MaintenancePlanFormValues>();

  // Selection states
  const [selectedComponent, setSelectedComponent] = useState<ComponentRead | null>(null);
  const [selectedMaintenance, setSelectedMaintenance] = useState<MaintenanceRead | null>(null);

  // Component modals/forms
  const [componentModalVisible, setComponentModalVisible] = useState(false);
  const [editingComponent, setEditingComponent] = useState<ComponentRead | null>(null);
  type ComponentFormValues = Omit<Partial<ComponentCreate & ComponentUpdate>, 'installed_date' | 'warranty_expiry'> & {
    installed_date?: dayjs.Dayjs;
    warranty_expiry?: dayjs.Dayjs;
  };

  const [componentForm] = Form.useForm<ComponentFormValues>();

  // Maintenance modals/forms
  const [maintenanceModalVisible, setMaintenanceModalVisible] = useState(false);
  const [editingMaintenance, setEditingMaintenance] = useState<MaintenanceRead | null>(null);
  type MaintenanceFormValues = Omit<Partial<MaintenanceCreate & MaintenanceUpdate>, 'scheduled_date' | 'completed_date'> & {
    scheduled_date?: dayjs.Dayjs;
    completed_date?: dayjs.Dayjs;
  };

  const [maintenanceForm] = Form.useForm<MaintenanceFormValues>();

  const loadData = useCallback(async () => {
    if (!assetId || Number.isNaN(assetId)) return;
    try {
      setLoading(true);
      // Fetch sequentially to log/debug each response separately
      let a = null;
      try {
        a = await assetService.getById(assetId);
        console.debug('asset loaded', a);
        setAsset(a);
      } catch (err) {
        console.error('Error loading asset', err);
        message.error('Error loading asset');
      }

      try {
        const comps = await componentService.getByAsset(assetId);
        console.debug('components loaded', comps);
        setComponents(Array.isArray(comps) ? comps : []);
      } catch (err) {
        console.error('Error loading components', err);
        message.error('Error loading components');
        setComponents([]);
      }

      try {
        const maints = await maintenanceService.getByAsset(assetId);
        console.debug('maintenances loaded', maints);
        setMaintenances(Array.isArray(maints) ? maints : []);
      } catch (err) {
        console.error('Error loading maintenances', err);
        message.error('Error loading maintenances');
        setMaintenances([]);
      }

      try {
        const plans = await maintenancePlanService.getByAsset(assetId);
        console.debug('maintenance plans loaded', plans);
        setMaintenancePlans(Array.isArray(plans) ? plans : []);
      } catch (err) {
        console.error('Error loading maintenance plans', err);
        message.error('Error loading maintenance plans');
        setMaintenancePlans([]);
      }

      try {
        const us = await userService.getAll();
        console.debug('users loaded', us?.length);
        setUsers(Array.isArray(us) ? us : []);
      } catch (err) {
        console.error('Error loading users', err);
        message.error('Error loading users');
        setUsers([]);
      }
    } catch (err) {
      console.error('Error loading asset detail:', err);
      message.error('Error loading asset details');
    } finally {
      setLoading(false);
    }
  }, [assetId, assetService, componentService, maintenanceService, maintenancePlanService, userService]);

  // Auth guard + data load
  useEffect(() => {
    if (!authLoading && !isAuthenticated) {
      router.push('/login');
      return;
    }
    if (isAuthenticated) {
      loadData();
    }
  }, [isAuthenticated, authLoading, router, loadData]);

  const COMPONENT_STATUS = [
    { value: 'Active', color: 'green' },
    { value: 'Inactive', color: 'red' },
    { value: 'Maintenance', color: 'orange' },
    { value: 'Retired', color: 'gray' },
  ];

  const MAINTENANCE_STATUS = [
    { value: 'scheduled', color: 'orange', label: 'Scheduled' },
    { value: 'in_progress', color: 'blue', label: 'In Progress' },
    { value: 'completed', color: 'green', label: 'Completed' },
    { value: 'cancelled', color: 'red', label: 'Cancelled' },
  ];

  const MAINTENANCE_TYPES = ['preventive', 'corrective', 'inspection'];

  const userMap = useMemo<Record<number, UserRead>>(() => {
    const map: Record<number, UserRead> = {};
    for (const u of users) map[u.id] = u;
    return map;
  }, [users]);

  if (authLoading || loading) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '50vh' }}>
        <Spin size="large" />
      </div>
    );
  }

  const formatCurrency = (value?: number) => (value == null ? '-' : new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(value));

  // Components table columns
  const componentColumns: ColumnsType<ComponentRead> = [
    { title: 'Name', dataIndex: 'name', key: 'name' },
    { title: 'Type', dataIndex: 'component_type', key: 'component_type' },
    { title: 'Status', dataIndex: 'status', key: 'status',
      render: (status: string) => (<Tag color={getComponentStatusColor(status)}>{formatLabel(status)}</Tag>)
    },
    { title: 'Model', dataIndex: 'model', key: 'model' },
    { title: 'Serial', dataIndex: 'serial_number', key: 'serial_number' },
    { title: 'Installed', dataIndex: 'installed_date', key: 'installed_date', render: (d?: string) => d ? dayjs(d).format('YYYY-MM-DD') : '-' },
    { title: 'Warranty', dataIndex: 'warranty_expiry', key: 'warranty_expiry', render: (d?: string) => d ? dayjs(d).format('YYYY-MM-DD') : '-' },
    { title: 'Value', dataIndex: 'current_value', key: 'current_value', align: 'right', render: (v?: number) => formatCurrency(v) },
  ];

  // Maintenances table columns
  const maintenanceColumns: ColumnsType<MaintenanceRead> = [
    { title: 'Type', dataIndex: 'maintenance_type', key: 'maintenance_type' },
  { title: 'Status', dataIndex: 'status', key: 'status', render: (s: string) => (<Tag color={getMaintenanceStatusColor(s)}>{formatLabel(MAINTENANCE_STATUS.find(x => x.value === s)?.label || s)}</Tag>) },
    { title: 'Technician', dataIndex: 'user_id', key: 'user_id', render: (id?: number) => id ? `${userMap[id]?.first_name} ${userMap[id]?.last_name}` : '-' },
    { title: 'Scheduled', dataIndex: 'scheduled_date', key: 'scheduled_date', render: (d?: string) => d ? dayjs(d).format('YYYY-MM-DD') : '-' },
    { title: 'Completed', dataIndex: 'completed_date', key: 'completed_date', render: (d?: string) => d ? dayjs(d).format('YYYY-MM-DD') : '-' },
    { title: 'Cost', dataIndex: 'cost', key: 'cost', align: 'right', render: (v?: number) => formatCurrency(v) },
  ];

  // Maintenance Plans table columns
  const formatFrequency = (p: MaintenancePlanRead): string => {
    if (p.frequency_days) return `${p.frequency_days} d`;
    if (p.frequency_weeks) return `${p.frequency_weeks} w`;
    if (p.frequency_months) return `${p.frequency_months} m`;
    return '-';
  };

  const maintenancePlanColumns: ColumnsType<MaintenancePlanRead> = [
    { title: 'Name', dataIndex: 'name', key: 'name', ellipsis: true },
    { title: 'Type', dataIndex: 'plan_type', key: 'plan_type', render: (v?: string) => v ? <Tag color={v === 'PREVENTIVE' ? 'blue' : v === 'INSPECTION' ? 'cyan' : 'purple'}>{formatLabel(v)}</Tag> : '-' },
    { title: 'Frequency', key: 'frequency', render: (_: unknown, r) => formatFrequency(r) },
    { title: 'Next Due', dataIndex: 'next_due_date', key: 'next_due_date', render: (d?: string) => d ? dayjs(d).format('YYYY-MM-DD') : '-' },
    { title: 'Active', dataIndex: 'active', key: 'active', render: (a?: boolean | null) => a ? <Tag color="green">Active</Tag> : <Tag color="red">Inactive</Tag> },
  ];

  // Components handlers
  const openCreateComponent = () => {
    setEditingComponent(null);
    componentForm.resetFields();
    setComponentModalVisible(true);
  };

  const openEditComponent = () => {
    if (!selectedComponent) return;
    setEditingComponent(selectedComponent);
    componentForm.setFieldsValue({
      ...selectedComponent,
      installed_date: selectedComponent.installed_date ? dayjs(selectedComponent.installed_date) : undefined,
      warranty_expiry: selectedComponent.warranty_expiry ? dayjs(selectedComponent.warranty_expiry) : undefined,
    } as ComponentFormValues);
    setComponentModalVisible(true);
  };

  const submitComponent = async (values: ComponentFormValues) => {
    try {
      const payload: Partial<ComponentCreate & ComponentUpdate> = {
        ...values,
        asset_id: assetId,
        installed_date: values.installed_date ? dayjs(values.installed_date).format('YYYY-MM-DD') : undefined,
        warranty_expiry: values.warranty_expiry ? dayjs(values.warranty_expiry).format('YYYY-MM-DD') : undefined,
      };
      if (editingComponent) {
        await componentService.update(editingComponent.id, payload as ComponentUpdate);
        message.success('Component updated');
      } else {
        await componentService.create(payload as ComponentCreate);
        message.success('Component created');
      }
      setComponentModalVisible(false);
      setEditingComponent(null);
      setSelectedComponent(null);
      // Reset to first page when data changes
      setComponentsPage(1);
      const list = await componentService.getByAsset(assetId);
      setComponents(list);
    } catch (e) {
      console.error(e);
      message.error('Error saving component');
    }
  };

  const deleteComponent = async () => {
    if (!selectedComponent) return;
    try {
      await componentService.delete(selectedComponent.id);
      message.success('Component deleted');
      setSelectedComponent(null);
      // Reset to first page when data changes
      setComponentsPage(1);
      const list = await componentService.getByAsset(assetId);
      setComponents(list);
    } catch (e) {
      console.error(e);
      message.error('Error deleting component');
    }
  };

  // Maintenance handlers
  const openCreateMaintenance = () => {
    setEditingMaintenance(null);
    maintenanceForm.resetFields();
    setMaintenanceModalVisible(true);
  };

  const openEditMaintenance = () => {
    if (!selectedMaintenance) return;
    setEditingMaintenance(selectedMaintenance);
    maintenanceForm.setFieldsValue({
      ...selectedMaintenance,
      scheduled_date: selectedMaintenance.scheduled_date ? dayjs(selectedMaintenance.scheduled_date) : undefined,
      completed_date: selectedMaintenance.completed_date ? dayjs(selectedMaintenance.completed_date) : undefined,
    } as MaintenanceFormValues);
    setMaintenanceModalVisible(true);
  };

  const submitMaintenance = async (values: MaintenanceFormValues) => {
    try {
      const payload: Partial<MaintenanceCreate & MaintenanceUpdate> = {
        ...values,
        asset_id: assetId,
        scheduled_date: values.scheduled_date ? dayjs(values.scheduled_date).toISOString() : undefined,
        completed_date: values.completed_date ? dayjs(values.completed_date).toISOString() : undefined,
      };
      if (editingMaintenance) {
        await maintenanceService.update(editingMaintenance.id, payload as MaintenanceUpdate);
        message.success('Maintenance updated');
      } else {
        // require user_id for create
        if (!('user_id' in payload) || !payload['user_id']) {
          message.error('Please select a technician');
          return;
        }
        await maintenanceService.create(payload as MaintenanceCreate);
        message.success('Maintenance created');
      }
      setMaintenanceModalVisible(false);
      setEditingMaintenance(null);
      setSelectedMaintenance(null);
      // Reset to first page when data changes
      setMaintenancesPage(1);
      const list = await maintenanceService.getByAsset(assetId);
      setMaintenances(list);
    } catch (e) {
      console.error(e);
      message.error('Error saving maintenance');
    }
  };

  if (!isAuthenticated) return null;

  const deleteMaintenance = async () => {
    if (!selectedMaintenance) return;
    try {
      await maintenanceService.delete(selectedMaintenance.id);
      message.success('Maintenance deleted');
      setSelectedMaintenance(null);
      // Reset to first page when data changes
      setMaintenancesPage(1);
      const list = await maintenanceService.getByAsset(assetId);
      setMaintenances(list);
    } catch (e) {
      console.error(e);
      message.error('Error deleting maintenance');
    }
  };

  // Delete maintenance plan placeholder (if needed later)

  // Maintenance Plan handlers
  const openCreateMaintenancePlan = () => {
    setEditingMaintenancePlan(null);
    maintenancePlanForm.resetFields();
    setMaintenancePlanModalVisible(true);
  };

  const openEditMaintenancePlan = (plan?: MaintenancePlanRead) => {
    if (!plan) return;
    setEditingMaintenancePlan(plan);
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const planData = plan as any;
    maintenancePlanForm.setFieldsValue({
      name: planData.name,
      description: planData.description,
      plan_type: planData.plan_type,
      frequency_days: planData.frequency_days,
      estimated_duration: planData.estimated_duration,
      estimated_cost: planData.estimated_cost,
      next_due_date: planData.next_due_date ? dayjs(planData.next_due_date) : undefined,
      component_id: planData.component_id,
    } as MaintenancePlanFormValues);
    setMaintenancePlanModalVisible(true);
  };

  const submitMaintenancePlan = async (values: MaintenancePlanFormValues) => {
    try {
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      const payload: any = {
        name: values.name,
        description: values.description || null,
        plan_type: values.plan_type, // This will be sent as string (PREVENTIVE, INSPECTION, PREDICTIVE)
        frequency_days: values.frequency_days || null,
        frequency_weeks: null, // Simplified: only use days
        frequency_months: null, // Simplified: only use days
        estimated_duration: values.estimated_duration || null,
        estimated_cost: values.estimated_cost || null,
        start_date: dayjs().toISOString(), // Set to current time as start
        next_due_date: values.next_due_date ? dayjs(values.next_due_date).toISOString() : null,
        last_execution_date: null, // Will be set when maintenance is completed
        active: true, // Always active when created
        asset_id: assetId,
        component_id: values.component_id || null,
      };
      
      if (editingMaintenancePlan) {
        await maintenancePlanService.update(editingMaintenancePlan.id, payload);
        message.success('Maintenance plan updated successfully');
      } else {
        await maintenancePlanService.create(payload);
        message.success('Maintenance plan created successfully');
      }
      
      setMaintenancePlanModalVisible(false);
      setEditingMaintenancePlan(null);
      maintenancePlanForm.resetFields();
      
      // Reset to first page when data changes
      setMaintenancePlansPage(1);
      // refresh list
      const list = await maintenancePlanService.getByAsset(assetId);
      setMaintenancePlans(Array.isArray(list) ? list : []);
    } catch (e) {
      console.error('Error saving maintenance plan:', e);
      message.error('Error saving maintenance plan');
    }
  };

  const deleteMaintenancePlan = async (plan?: MaintenancePlanRead) => {
    if (!plan) return;
    try {
      await maintenancePlanService.delete(plan.id);
      message.success('Maintenance plan deleted');
      // Reset to first page when data changes
      setMaintenancePlansPage(1);
      const list = await maintenancePlanService.getByAsset(assetId);
      setMaintenancePlans(Array.isArray(list) ? list : []);
    } catch (e) {
      console.error(e);
      message.error('Error deleting maintenance plan');
    }
  };

  // Replace UI: Descriptions + Tabs with EntityList inside each TabPane

  const tabs: TabDef[] = [
    {
      key: 'components',
      tab: `Components (${components.length})`,
      content: (
        <EntityList
          title={`Components (${components.length})`}
          data={components}
          columns={componentColumns}
          rowKey="id"
          onCreate={openCreateComponent}
          onEdit={(r) => { setSelectedComponent(r); openEditComponent(); }}
          onDelete={async (r) => { setSelectedComponent(r as ComponentRead); await deleteComponent(); }}
          onView={(r) => setSelectedComponent(r as ComponentRead)}
          pagination={{ 
            current: componentsPage, 
            pageSize: componentsPageSize, 
            total: components.length 
          }}
          onChangePage={handleComponentsPageChange}
        />
      ),
    },
    {
      key: 'maintenances',
      tab: `Maintenances (${maintenances.length})`,
      content: (
        <EntityList
          title={`Maintenances (${maintenances.length})`}
          data={maintenances}
          columns={maintenanceColumns}
          rowKey="id"
          onCreate={openCreateMaintenance}
          onEdit={(r) => { setSelectedMaintenance(r); openEditMaintenance(); }}
          onDelete={async (r) => { setSelectedMaintenance(r as MaintenanceRead); /* reuse deleteMaintenance */ await deleteMaintenance(); }}
          onView={(r) => setSelectedMaintenance(r as MaintenanceRead)}
          pagination={{ 
            current: maintenancesPage, 
            pageSize: maintenancesPageSize, 
            total: maintenances.length 
          }}
          onChangePage={handleMaintenancesPageChange}
        />
      ),
    },
    {
      key: 'plans',
      tab: `Maintenance Plans (${maintenancePlans.length})`,
      content: (
        <EntityList
          title={`Maintenance Plans (${maintenancePlans.length})`}
          data={maintenancePlans}
          columns={maintenancePlanColumns}
          rowKey="id"
          onCreate={openCreateMaintenancePlan}
          onEdit={(r) => openEditMaintenancePlan(r as MaintenancePlanRead)}
          onDelete={async (r) => { await deleteMaintenancePlan(r as MaintenancePlanRead); }}
          pagination={{ 
            current: maintenancePlansPage, 
            pageSize: maintenancePlansPageSize, 
            total: maintenancePlans.length 
          }}
          onChangePage={handleMaintenancePlansPageChange}
        />
      ),
    },
  ];

  return (
    <>
      <DetailWithTabs
        backHref="/asset"
        title={asset ? `${asset.name || asset.id}` : 'Asset'}
        descriptions={
          <Descriptions className='mt-1' bordered size="small" column={3}>
            <Descriptions.Item label="Id">{asset?.id || '-'}</Descriptions.Item>
            <Descriptions.Item label="Type">{asset?.asset_type || '-'}</Descriptions.Item>
            <Descriptions.Item label="Status">{asset ? <Tag color={getComponentStatusColor(asset.status)}>{formatLabel(asset.status)}</Tag> : '-'}</Descriptions.Item>
            <Descriptions.Item label="Location">{asset?.location || '-'}</Descriptions.Item>
            <Descriptions.Item label="Model">{asset?.model || '-'}</Descriptions.Item>
            <Descriptions.Item label="Serial Number">{asset?.serial_number || '-'}</Descriptions.Item>
            <Descriptions.Item label="Purchase Cost">{formatCurrency(asset?.purchase_cost)}</Descriptions.Item>
            <Descriptions.Item label="Current Value">{formatCurrency(asset?.current_value)}</Descriptions.Item>
            <Descriptions.Item label="Purchase Date">{asset?.purchase_date ? dayjs(asset.purchase_date).format('YYYY-MM-DD') : '-'}</Descriptions.Item>
          </Descriptions>
        }
        tabs={tabs}
      />

      <ModalDialog
        open={componentModalVisible}
        title={editingComponent ? 'Edit Component' : 'Add Component'}
        onClose={() => { setComponentModalVisible(false); setEditingComponent(null); }}
        width={720}
        primary={{ label: editingComponent ? 'Update' : 'Create', onClick: () => componentForm.submit() }}
        secondary={{ label: 'Cancel', onClick: () => { setComponentModalVisible(false); setEditingComponent(null); } }}
      >
        <Form form={componentForm} layout="vertical" onFinish={submitComponent}>
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item name="name" label="Name" rules={[{ required: true, message: 'Please enter name' }]}>
                <Input placeholder="Component name" />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="component_type" label="Type" rules={[{ required: true, message: 'Please select type' }]}>
                <Select placeholder="Select type" options={['Electrical','Mechanical','Hydraulic','Other'].map(t=>({value:t,label:t}))} />
              </Form.Item>
            </Col>
          </Row>
          <Form.Item name="description" label="Description">
            <Input.TextArea rows={3} placeholder="Description" />
          </Form.Item>
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item name="model" label="Model">
                <Input />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="serial_number" label="Serial Number">
                <Input />
              </Form.Item>
            </Col>
          </Row>
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item name="status" label="Status" initialValue="Active">
                <Select placeholder="Select status" options={COMPONENT_STATUS.map(s=>({value:s.value,label:s.value}))} />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="location" label="Location">
                <Input />
              </Form.Item>
            </Col>
          </Row>
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item name="installed_date" label="Installed Date">
                <DatePicker className="w-full" />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="warranty_expiry" label="Warranty Expiry">
                <DatePicker className="w-full" />
              </Form.Item>
            </Col>
          </Row>
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item name="purchase_cost" label="Purchase Cost">
                <InputNumber className="w-full" min={0} />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="current_value" label="Current Value">
                <InputNumber className="w-full" min={0} />
              </Form.Item>
            </Col>
          </Row>
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item name="maintenance_interval_days" label="Maintenance Interval (days)">
                <InputNumber className="w-full" min={0} />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="responsible_id" label="Responsible">
                <Select allowClear placeholder="Select user" options={users.map(u=>({value:u.id,label:`${u.first_name} ${u.last_name}`}))} />
              </Form.Item>
            </Col>
          </Row>
        </Form>
      </ModalDialog>

      {/* Maintenance Plan Create/Edit Modal - Simplified */}
      <ModalDialog
        open={maintenancePlanModalVisible}
        title={editingMaintenancePlan ? 'Edit Maintenance Plan' : 'Create Maintenance Plan'}
        onClose={() => { setMaintenancePlanModalVisible(false); setEditingMaintenancePlan(null); }}
        width={600}
        primary={{ label: editingMaintenancePlan ? 'Update Plan' : 'Create Plan', onClick: () => maintenancePlanForm.submit() }}
        secondary={{ label: 'Cancel', onClick: () => { setMaintenancePlanModalVisible(false); setEditingMaintenancePlan(null); } }}
      >
        <Form form={maintenancePlanForm} layout="vertical" onFinish={submitMaintenancePlan}>
          <Form.Item name="name" label="Plan Name" rules={[{ required: true, message: 'Please enter plan name' }]}> 
            <Input placeholder="e.g., Monthly Safety Inspection" />
          </Form.Item>
          
          <Form.Item name="description" label="Description">
            <Input.TextArea rows={2} placeholder="Brief description of the maintenance plan..." />
          </Form.Item>
          
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item name="plan_type" label="Plan Type" rules={[{ required: true, message: 'Please select type' }]}> 
                <Select placeholder="Select type" options={[
                  {value: 'PREVENTIVE', label: '🔧 Preventive'}, 
                  {value: 'INSPECTION', label: '🔍 Inspection'},
                  {value: 'PREDICTIVE', label: '📊 Predictive'}
                ]} />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="frequency_days" label="Frequency (days)" rules={[{ required: true, message: 'Please enter frequency' }]}>
                <InputNumber className="w-full" min={1} max={365} placeholder="30" 
                  addonAfter="days" />
              </Form.Item>
            </Col>
          </Row>
          
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item name="estimated_duration" label="Estimated Duration (hours)">
                <InputNumber className="w-full" min={0.1} step={0.5} placeholder="2.0" />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="estimated_cost" label="Estimated Cost ($)">
                <InputNumber className="w-full" min={0} step={10} placeholder="150" />
              </Form.Item>
            </Col>
          </Row>
          
          <Form.Item name="next_due_date" label="Next Due Date" rules={[{ required: true, message: 'Please select next due date' }]}>
            <DatePicker 
              className="w-full" 
              showTime={{format: 'HH:mm'}}
              format="YYYY-MM-DD HH:mm"
              placeholder="When is the next maintenance due?"
            />
          </Form.Item>
          
          <Form.Item name="component_id" label="Specific Component (Optional)">
            <Select allowClear placeholder="Select component if maintenance is for a specific part" 
              options={components.map(c=>({value:c.id,label:`${c.name} (ID: ${c.id})`}))} />
          </Form.Item>
        </Form>
      </ModalDialog>
      <ModalDialog
        title={editingMaintenance ? 'Edit Maintenance' : 'Add Maintenance'}
        open={maintenanceModalVisible}
        onClose={() => { setMaintenanceModalVisible(false); setEditingMaintenance(null); }}
        width={720}
        primary={{ label: editingMaintenance ? 'Update' : 'Create', onClick: () => maintenanceForm.submit() }}
        secondary={{ label: 'Cancel', onClick: () => { setMaintenanceModalVisible(false); setEditingMaintenance(null); } }}
      >
        <Form form={maintenanceForm} layout="vertical" onFinish={submitMaintenance}>
          <Form.Item name="description" label="Description" rules={[{ required: true, message: 'Please enter description' }]}>
            <Input.TextArea rows={3} placeholder="Description" />
          </Form.Item>
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item name="maintenance_type" label="Type" initialValue="preventive">
                <Select placeholder="Select type" options={MAINTENANCE_TYPES.map(t=>({value:t,label:t}))} />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="status" label="Status" initialValue="scheduled">
                <Select placeholder="Select status" options={MAINTENANCE_STATUS.map(s=>({value:s.value,label:s.label}))} />
              </Form.Item>
            </Col>
          </Row>
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item name="user_id" label="Technician" rules={editingMaintenance ? [] : [{ required: true, message: 'Please select a technician' }]}>
                <Select allowClear placeholder="Select user" options={users.map(u=>({value:u.id,label:`${u.first_name} ${u.last_name}`}))} />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="scheduled_date" label="Scheduled Date">
                <DatePicker className="w-full" />
              </Form.Item>
            </Col>
          </Row>
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item name="duration_hours" label="Duration (hours)">
                <InputNumber className="w-full" min={0} />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="cost" label="Cost">
                <InputNumber className="w-full" min={0} />
              </Form.Item>
            </Col>
          </Row>
          <Form.Item name="notes" label="Notes">
            <Input.TextArea rows={3} />
          </Form.Item>
        </Form>
      </ModalDialog>
    </>
  );
}
