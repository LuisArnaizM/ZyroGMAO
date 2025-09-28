'use client';

import React, { useEffect, useState, useCallback, useMemo } from 'react';
import { Tag, Form, Input, Select, DatePicker, InputNumber, message, Row, Col, Space, Badge, Tooltip, Segmented } from 'antd';
import { CheckCircleOutlined, ClockCircleOutlined, ExclamationCircleOutlined, UserOutlined, ToolOutlined, FileTextOutlined, WarningOutlined, BellOutlined, PlusOutlined } from '@ant-design/icons';
import type { ColumnsType } from 'antd/es/table';
import dayjs from 'dayjs';
import { apiClient } from '../utils/api-client';
import { ManagementPageLayout } from '../components/layout/ManagementPageLayout';
import { useAppDispatch, useAppSelector } from '../store/hooks';
import { fetchWorkordersKpi } from '../store/slices/kpiSlice';
import { EntityList } from '../components/data/EntityList';
import { WorkOrderService } from '../services/workorder.service';
import { MaintenancePlanService, MaintenancePlanRead } from '../services/maintenancePlan.service';
import ModalDialog from '../components/ui/ModalDialog';
import { AssetService } from '../services/asset.service';
import { UserService } from '../services/user.service';
import { WorkOrderRead, WorkOrderCreate, WorkOrderUpdate, WorkOrderStatus, WorkOrderPriority, AssetRead, UserRead } from '../types';
import { getWorkOrderStatusColor, getWorkOrderPriorityColor, formatLabel, getWorkOrderTypeColor } from '../utils/labels';
import { AppButton } from '../components/ui/AppButton';

const { TextArea } = Input;
const { Option } = Select;

const WORK_ORDER_TYPES = ['REPAIR','INSPECTION','MAINTENANCE'];
const WORK_ORDER_STATUS = [
  { value: WorkOrderStatus.OPEN, color: 'gray', label: 'Open' },
  { value: WorkOrderStatus.ASSIGNED, color: 'orange', label: 'Assigned' },
  { value: WorkOrderStatus.IN_PROGRESS, color: 'blue', label: 'In Progress' },
  { value: WorkOrderStatus.COMPLETED, color: 'green', label: 'Completed' },
  { value: WorkOrderStatus.CANCELLED, color: 'red', label: 'Cancelled' }
];
const WORK_ORDER_PRIORITIES = [
  { value: WorkOrderPriority.LOW, color: 'green', label: 'Low' },
  { value: WorkOrderPriority.MEDIUM, color: 'orange', label: 'Medium' },
  { value: WorkOrderPriority.HIGH, color: 'red', label: 'High' }
];

const WorkOrderPage: React.FC = () => {
  const [workOrders, setWorkOrders] = useState<WorkOrderRead[]>([]);
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(20);
  const [total, setTotal] = useState<number | undefined>(undefined);
  const [assets, setAssets] = useState<AssetRead[]>([]);
  const [allUsers, setAllUsers] = useState<UserRead[]>([]);
  const [managers, setManagers] = useState<UserRead[]>([]);
  const [loading, setLoading] = useState(false);
  const [modalVisible, setModalVisible] = useState(false);
  const [editingWorkOrder, setEditingWorkOrder] = useState<WorkOrderRead | null>(null);
  const workorderKpi = useAppSelector(s => s.kpi.workorders);
  const dispatch = useAppDispatch();
  const [form] = Form.useForm();

  // Notifications (Upcoming plans)
  const [upcomingPlans, setUpcomingPlans] = useState<MaintenancePlanRead[]>([]);
  const [notificationsOpen, setNotificationsOpen] = useState(false);
  const [windowDays, setWindowDays] = useState<number>(30);
  const windowOptions = [7,14,30,60];

  const workOrderService = useMemo(() => new WorkOrderService(apiClient), []);
  const assetService = new AssetService();
  const userService = new UserService();

  useEffect(() => { (async()=> { await Promise.all([fetchWorkOrders(page,pageSize), fetchAssets(), fetchUsersData()]); })(); /* eslint-disable-line */ }, []);

  const fetchWorkOrders = useCallback(async (p: number = page, ps: number = pageSize) => {
    try {
      setLoading(true);
      const response = await workOrderService.getWorkOrders({ pagination: { page: p, page_size: ps } });
      if (response.success && response.data) {
        setWorkOrders(response.data);
        const computedTotal = response.data.length === ps ? p * ps + 1 : (p - 1) * ps + response.data.length;
        setTotal(computedTotal);
      } else setWorkOrders([]);
    } catch (e) {
      console.error(e); message.error('Error loading work orders');
    } finally { setLoading(false); }
  }, [page,pageSize,workOrderService]);

  const fetchAssets = async () => { try { const data = await assetService.getAll(); setAssets(Array.isArray(data)?data:[]);} catch(e){console.error(e);} };
  const fetchUsersData = async () => { try { const all = await userService.getAll(); setAllUsers(Array.isArray(all)?all:[]); const mgr = await userService.getManagers(); setManagers(Array.isArray(mgr)?mgr:[]);} catch(e){console.error(e);} };

  const fetchUpcomingMaintenancePlans = useCallback(async (days?: number) => {
    try {
      const svc = new MaintenancePlanService();
      const plans = await svc.getUpcoming({ window_days: days || windowDays });
      const ordered = [...plans].sort((a: MaintenancePlanRead, b: MaintenancePlanRead)=> dayjs(a.next_due_date).unix()-dayjs(b.next_due_date).unix());
      setUpcomingPlans(ordered);
    } catch(e){ console.error('Error fetching upcoming plans', e);} 
  }, [windowDays]);

  // Now that fetchUpcomingMaintenancePlans is declared, run effect
  useEffect(() => { if (assets.length>0) fetchUpcomingMaintenancePlans(windowDays); }, [assets, windowDays, fetchUpcomingMaintenancePlans]);

  const getUserName = (id?: number) => { const u = allUsers.find(x=>x.id===id); return u? `${u.first_name} ${u.last_name}`:'No assigned'; };
  const getAssetName = (id: number) => assets.find(a=>a.id===id)?.name || 'Asset not found';

  const createWorkOrderFromPlan = useCallback(async (plan: MaintenancePlanRead) => {
    try {
      const p = plan; const asset = assets.find(a=>a.id===p.asset_id); if(!asset){ message.error('Asset not found for plan'); return; }
      const workOrderData: WorkOrderCreate = {
        title: `${p.plan_type?.toUpperCase() || 'MAINTENANCE'}: ${p.name}`,
        description: `Maintenance work order created from plan: ${p.name}${p.description? '\n\n'+p.description:''}`,
        work_type: (p.plan_type?.toUpperCase()==='PREVENTIVE'?'MAINTENANCE': p.plan_type?.toUpperCase()==='CORRECTIVE'?'REPAIR':'INSPECTION') as 'REPAIR'|'INSPECTION'|'MAINTENANCE',
        asset_id: p.asset_id || 0,
        status: WorkOrderStatus.OPEN,
        priority: WorkOrderPriority.MEDIUM,
        scheduled_date: p.next_due_date,
        plan_id: p.id
      };
      const result = await workOrderService.createWorkOrder(workOrderData);
      if(result.success){
        message.success('Work order created');
        // Ya no ocultamos manualmente; backend dejará de devolverlo.
        fetchWorkOrders(page,pageSize);
        fetchUpcomingMaintenancePlans(windowDays);
      }
    } catch(e){ console.error(e); message.error('Failed to create work order'); }
  }, [assets, workOrderService, page, pageSize, fetchWorkOrders, fetchUpcomingMaintenancePlans, windowDays]);

  const handleCreate = () => { setEditingWorkOrder(null); form.resetFields(); setModalVisible(true); };
  const handleEdit = (wo: WorkOrderRead) => { setEditingWorkOrder(wo); form.setFieldsValue({ ...wo, scheduled_date: wo.scheduled_date? dayjs(wo.scheduled_date): null }); setModalVisible(true); };
  const handleDelete = async (id: number) => { try { await workOrderService.deleteWorkOrder(id); message.success('Deleted'); await fetchWorkOrders(); dispatch(fetchWorkordersKpi()); } catch(e){ console.error(e); message.error('Delete error'); } };
  const handleView = (wo: WorkOrderRead) => { window.location.href = `/workorders/${wo.id}`; };

  const handleSubmit = async (values: Partial<WorkOrderCreate & WorkOrderUpdate>) => {
    try {
      const payload: WorkOrderCreate | WorkOrderUpdate = { ...values, scheduled_date: values.scheduled_date? dayjs(values.scheduled_date).toISOString(): undefined };
      if (editingWorkOrder) { await workOrderService.updateWorkOrder(editingWorkOrder.id, payload); message.success('Updated'); }
      else { await workOrderService.createWorkOrder(payload as WorkOrderCreate); message.success('Created'); }
      setModalVisible(false); form.resetFields(); await fetchWorkOrders(); dispatch(fetchWorkordersKpi());
    } catch(e){ console.error(e); message.error('Save error'); }
  };
  const handleModalCancel = () => { setModalVisible(false); setEditingWorkOrder(null); form.resetFields(); };

  const columns: ColumnsType<WorkOrderRead> = [
    { title:'ID', dataIndex:'id', key:'id', width:80, sorter:(a,b)=>a.id-b.id },
    { title:'Title', dataIndex:'title', key:'title', width:220, ellipsis:true, sorter:(a,b)=> a.title.localeCompare(b.title) },
    { title:'Asset', dataIndex:'asset_id', key:'asset_id', width:160, render:(id:number)=> getAssetName(id), filters: assets.map(a=>({text:a.name,value:a.id})), onFilter:(v,r)=> r.asset_id===v },
    { title:'Type', dataIndex:'work_type', key:'work_type', width:140, render:(t:string)=>(<Tag icon={<ToolOutlined />} color={getWorkOrderTypeColor(t)}>{formatLabel(t)}</Tag>), filters: WORK_ORDER_TYPES.map(t=>({text:t,value:t})), onFilter:(v,r)=> r.work_type===v },
    { title:'Status', dataIndex:'status', key:'status', width:140, render:(s:WorkOrderStatus)=> { const color = getWorkOrderStatusColor(s as unknown as string); const raw = WORK_ORDER_STATUS.find(x=>x.value===s)?.label || String(s); return <Tag color={color}>{formatLabel(raw)}</Tag>; }, filters: WORK_ORDER_STATUS.map(s=>({text:s.label,value:s.value})), onFilter:(v,r)=> r.status===v },
    { title:'Priority', dataIndex:'priority', key:'priority', width:140, render:(p:WorkOrderPriority)=> { const color = getWorkOrderPriorityColor(p as unknown as string); const raw = WORK_ORDER_PRIORITIES.find(x=>x.value===p)?.label || String(p); return <Tag color={color}>{formatLabel(raw)}</Tag>; }, filters: WORK_ORDER_PRIORITIES.map(p=>({text:p.label,value:p.value})), onFilter:(v,r)=> r.priority===v },
    { title:'Assigned To', dataIndex:'assigned_to', key:'assigned_to', width:200, render:(id?:number)=>(<span><UserOutlined style={{marginRight:8}} />{getUserName(id)}</span>) },
    { title:'Scheduled Date', dataIndex:'scheduled_date', key:'scheduled_date', width:160, render:(d:string)=> d? dayjs(d).format('DD/MM/YYYY'):'-', sorter:(a,b)=> { if(!a.scheduled_date && !b.scheduled_date) return 0; if(!a.scheduled_date) return 1; if(!b.scheduled_date) return -1; return dayjs(a.scheduled_date).unix()-dayjs(b.scheduled_date).unix(); } }
  ];

  return (
    <ManagementPageLayout
      kpis={[
        { title:'Total Work Orders', value: workorderKpi?.total ?? 0, prefix:<FileTextOutlined/> },
        { title:'Overdue', value: workorderKpi?.overdue ?? 0, prefix:<ClockCircleOutlined style={{color:'#faad14'}}/>, valueStyle:{color:'#faad14'} },
        { title:'In Progress', value: workorderKpi?.in_progress ?? 0, prefix:<ExclamationCircleOutlined style={{color:'#1890ff'}}/>, valueStyle:{color:'#1890ff'} },
        { title:'Completed', value: workorderKpi?.completed ?? 0, prefix:<CheckCircleOutlined style={{color:'#52c41a'}}/>, valueStyle:{color:'#52c41a'} },
        { title:'Open', value: workorderKpi?.draft ?? 0, prefix:<FileTextOutlined style={{color:'#8c8c8c'}}/>, valueStyle:{color:'#8c8c8c'} },
        { title:'Cancelled', value: workorderKpi?.cancelled ?? 0, prefix:<WarningOutlined style={{color:'#f5222d'}}/>, valueStyle:{color:'#f5222d'} }
      ]}
      headerActions={
        <div className="notification-bell-wrapper">
          <Tooltip title={upcomingPlans.length ? 'Planes de mantenimiento próximos' : 'No hay planes próximos'}>
            <Badge
              count={upcomingPlans.length}
              overflowCount={99}
              color={upcomingPlans.some(p => dayjs(p.next_due_date).diff(dayjs(),'days') < 0) ? 'red' : (upcomingPlans.some(p => dayjs(p.next_due_date).diff(dayjs(),'days') <=3)? 'orange':'#f59856')}
            >
              <button
                onClick={()=> setNotificationsOpen(true)}
                className={`notification-bell-btn ${upcomingPlans.length ? 'notification-bell-active':''}`}
                aria-label="Notificaciones de planes de mantenimiento"
                type="button"
              >
                <BellOutlined style={{ fontSize: 26 }} />
              </button>
            </Badge>
          </Tooltip>
        </div>
      }
    >
      <EntityList<WorkOrderRead>
        title="Work Orders List"
        data={workOrders}
        columns={columns}
        rowKey="id"
        loading={loading}
        createLabel="Add New Work Order"
        onCreate={handleCreate}
        onView={row => handleView(row)}
        onEdit={row => handleEdit(row)}
        onDelete={row => handleDelete(row.id)}
        pagination={{ current: page, pageSize, total }}
        onChangePage={(p,ps)=> { setPage(p); setPageSize(ps); fetchWorkOrders(p,ps); }}
        scrollX={1000}
      />

      <ModalDialog
        className="notifications-modal"
        open={notificationsOpen}
        onClose={()=> setNotificationsOpen(false)}
        footer={null}
        title={
          <Space wrap>
            <BellOutlined />
            <span className="tracking-wide">Planes próximos</span>
            <Badge count={upcomingPlans.length} color="#f59856" />
            <Segmented size="small" value={windowDays} options={windowOptions.map(d=>({label:`${d}d`, value:d}))} onChange={v=> setWindowDays(Number(v))} />
          </Space>
        }
        width={1000}
      >
        <Row gutter={[14,14]}>
          {upcomingPlans.map(plan => { const p = plan; const asset = assets.find(a=>a.id===p.asset_id); const daysUntil = dayjs(p.next_due_date).diff(dayjs(),'days'); const overdue=daysUntil<0; const urgent=!overdue && daysUntil<=3; const statusClass = overdue? 'overdue' : urgent? 'urgent':'safe'; return (
            <Col key={p.id} xs={24} sm={12} md={8} lg={6}>
              <div className={`plan-card ${statusClass}`}>
                <div className="flex justify-between gap-2 items-start mb-1">
                  <Tooltip title={p.name}><span className="font-medium truncate flex-1 text-sm leading-snug">{p.name}</span></Tooltip>
                  <span className="plan-tag uppercase">{p.plan_type}</span>
                </div>
                <div className="plan-meta"><span>Asset</span><span>{asset?.name||'-'}</span></div>
                <div className="plan-meta"><span>Due</span><span>{p.next_due_date? dayjs(p.next_due_date).format('DD/MM'): '-'}</span></div>
                <div className={`plan-status ${statusClass}`}>{overdue? `${Math.abs(daysUntil)} días vencido` : `${daysUntil} días`}</div>
                {p.estimated_duration && <div className="plan-meta"><span>Duración</span><span>{p.estimated_duration}h</span></div>}
                {p.estimated_cost && <div className="plan-meta"><span>Coste</span><span>€{p.estimated_cost}</span></div>}
                <div className="plan-actions">
                  <AppButton
                    variant="primary"
                    size="sm"
                    icon={<PlusOutlined />}
                    className="w-full"
                    onClick={()=> createWorkOrderFromPlan(plan)}
                  >Crear WO</AppButton>
                </div>
              </div>
            </Col> ); })}
        </Row>
        {upcomingPlans.length===0 && <div className="text-center text-sm text-muted py-8">No hay planes en los próximos {windowDays} días.</div>}
      </ModalDialog>

      <ModalDialog
        open={modalVisible}
        title={editingWorkOrder ? 'Edit Work Order' : 'Create New Work Order'}
        onClose={handleModalCancel}
        width={800}
        primary={{ label: editingWorkOrder ? 'Update' : 'Create', onClick: () => form.submit() }}
        secondary={{ label: 'Cancel', onClick: handleModalCancel }}
      >
        <Form form={form} layout="vertical" onFinish={handleSubmit} initialValues={{ status: WorkOrderStatus.OPEN, priority: WorkOrderPriority.MEDIUM }}>
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item name="title" label="Title" rules={[{ required: true, message: 'Please enter work order title' }]}>
                <Input placeholder="Enter work order title" />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="work_type" label="Work Type" rules={[{ required: true, message: 'Please select work type' }]}>
                <Select placeholder="Select work type">{WORK_ORDER_TYPES.map(t=><Option key={t} value={t}>{t}</Option>)}</Select>
              </Form.Item>
            </Col>
          </Row>
          <Form.Item name="description" label="Description"><TextArea rows={3} placeholder="Enter work order description" /></Form.Item>
          <Row gutter={16}>
            <Col span={8}>
              <Form.Item name="asset_id" label="Asset" rules={[{ required: true, message: 'Please select an asset' }]}>
                <Select placeholder="Select asset">{assets.map(a=> <Option key={a.id} value={a.id}>{a.name}</Option>)}</Select>
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item name="status" label="Status" rules={[{ required: true, message: 'Please select status' }]}>
                <Select placeholder="Select status">{WORK_ORDER_STATUS.map(s=> <Option key={s.value} value={s.value}>{s.label}</Option>)}</Select>
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item name="priority" label="Priority" rules={[{ required: true, message: 'Please select priority' }]}>
                <Select placeholder="Select priority">{WORK_ORDER_PRIORITIES.map(p=> <Option key={p.value} value={p.value}>{p.label}</Option>)}</Select>
              </Form.Item>
            </Col>
          </Row>
          <Row gutter={16}>
            <Col span={8}>
              <Form.Item name="assigned_to" label="Assigned To" rules={[{ required: true, message: 'Please select a manager' }]}>
                <Select allowClear placeholder="Select manager">{managers.map(u=> <Option key={u.id} value={u.id}>{u.first_name} {u.last_name}</Option>)}</Select>
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item name="scheduled_date" label="Scheduled Date"><DatePicker style={{width:'100%'}} /></Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item name="estimated_hours" label="Estimated Hours"><InputNumber min={0} style={{width:'100%'}} placeholder="0" /></Form.Item>
            </Col>
          </Row>
          <Row gutter={16}>
            <Col span={12}><Form.Item name="estimated_cost" label="Estimated Cost"><InputNumber min={0} style={{width:'100%'}} placeholder="0.00" /></Form.Item></Col>
            <Col span={12}><Form.Item name="actual_cost" label="Actual Cost"><InputNumber min={0} style={{width:'100%'}} placeholder="0.00" /></Form.Item></Col>
          </Row>
        </Form>
      </ModalDialog>
    </ManagementPageLayout>
  );
};

export default WorkOrderPage;