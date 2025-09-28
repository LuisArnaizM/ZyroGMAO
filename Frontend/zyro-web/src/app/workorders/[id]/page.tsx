'use client';

import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import {
  Button,
  Card,
  Col,
  Descriptions,
  Form,
  Input,
  InputNumber,
  Row,
  Select,
  Space,
  Spin,
  Tag,
  Typography,
  message,
  Divider,
  Tooltip,
} from 'antd';
import { ToolOutlined, UserOutlined, CheckCircleOutlined, PlusOutlined, DeleteOutlined, InfoCircleOutlined } from '@ant-design/icons';
import dayjs from 'dayjs';
import { useAuth } from '../../hooks/useAuth';
import { WorkOrderService } from '../../services/workorder.service';
import { TaskService } from '../../services/task.service';
import { AssetService } from '../../services/asset.service';
import { ComponentService } from '../../services/component.service';
import { UserService } from '../../services/user.service';
import { apiClient } from '../../utils/api-client';
import type { ColumnsType } from 'antd/es/table';
import { EntityList } from '../../components/data/EntityList';
import type {
  WorkOrderRead,
  TaskRead,
  TaskCreate,
  TaskUpdate,
  UserRead,
  AssetRead,
} from '../../types';
import { TaskStatus, TaskPriority } from '../../types';
import { getWorkOrderStatusColor, getWorkOrderPriorityColor } from '../../utils/labels';
import DetailWithTabs, { TabDef } from '../../components/layout/DetailWithTabs';
import { /* MaintenancePlanService */ } from '../../services/maintenancePlan.service';
import { AppButton } from '../../components/ui/AppButton';
import ModalDialog from '../../components/ui/ModalDialog';

const { Text } = Typography;
const { Option } = Select;
const { TextArea } = Input;

// Work order status/priority mappings are handled by utils/labels

export default function WorkOrderDetailPage() {
  const params = useParams();
  const router = useRouter();
  const { isAuthenticated, loading: authLoading, user } = useAuth();

  const workOrderId = useMemo(() => {
    const raw = params?.id as string | string[] | undefined;
    const idStr = Array.isArray(raw) ? raw[0] : raw;
    return idStr ? Number(idStr) : NaN;
  }, [params]);

  const workOrderService = useMemo(() => new WorkOrderService(apiClient), []);
  const taskService = useMemo(() => new TaskService(apiClient), []);
  const assetService = useMemo(() => new AssetService(), []);
  const componentService = useMemo(() => new ComponentService(), []);
  const userService = useMemo(() => new UserService(), []);
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [workOrder, setWorkOrder] = useState<WorkOrderRead | null>(null);
  const [tasks, setTasks] = useState<TaskRead[]>([]);
  const [users, setUsers] = useState<UserRead[]>([]);
  const [assets, setAssets] = useState<AssetRead[]>([]);
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(5);
  const [total, setTotal] = useState<number | undefined>(undefined);
  const [taskModalVisible, setTaskModalVisible] = useState(false);
  const [editingTask, setEditingTask] = useState<TaskRead | null>(null);
  const [taskForm] = Form.useForm();
  const [completeForm] = Form.useForm();
  const [completeModalVisible, setCompleteModalVisible] = useState(false);
  const [completingTask, setCompletingTask] = useState<TaskRead | null>(null);
  const [availableComponents, setAvailableComponents] = useState<{ id: number; name: string }[]>([]);
  const [componentErrors, setComponentErrors] = useState<Record<number, string>>({});
  const [completeWorkOrderModalVisible, setCompleteWorkOrderModalVisible] = useState(false);
  const [maintenanceForm] = Form.useForm();

  const formatLabel = (value: string): string => {
    if (!value) return '';
    return value.charAt(0).toUpperCase() + value.slice(1).toLowerCase();
  };

  const getTaskStatusColor = (status: string): string => {
    switch (status?.toLowerCase()) {
      case 'pending': return 'orange';
      case 'in_progress': return 'blue';
      case 'completed': return 'green';
      case 'cancelled': return 'red';
      default: return 'default';
    }
  };

  // Helper para obtener colores de prioridad
  const getSeverityColor = (priority: string): string => {
    switch (priority?.toLowerCase()) {
      case 'low': return 'green';
      case 'medium': return 'orange';
      case 'high': return 'red';
      case 'critical': return 'purple';
      default: return 'default';
    }
  };

  const getUserName = (userId?: number): string => {
    const user = users.find(u => u.id === userId);
    return user ? `${user.first_name} ${user.last_name}` : 'No assigned';
  };

  const getAssetName = (assetId?: number): string => {
    const asset = assets.find(a => a.id === assetId);
    return asset ? asset.name : '-';
  };

  const loadData = useCallback(async () => {
    if (!workOrderId || Number.isNaN(workOrderId)) return;
    try {
      setLoading(true);
      const [woResp, usersList, assetsList] = await Promise.all([
        workOrderService.getWorkOrder(workOrderId),
        userService.getAll(),
        assetService.getAll(),
      ]);
      if (woResp.success && woResp.data) {
        setWorkOrder(woResp.data);
      } else {
        setWorkOrder(null);
      }

      setUsers(Array.isArray(usersList) ? usersList : []);
      setAssets(Array.isArray(assetsList) ? assetsList : []);

      // Cargar componentes disponibles del activo de la WO (para completar tareas)
      try {
        const wo = woResp.success ? woResp.data : null;
        if (wo && wo.asset_id) {
          const comps = await componentService.getByAsset(wo.asset_id);
          setAvailableComponents(comps.map(c => ({ id: c.id, name: c.name })));
        } else {
          setAvailableComponents([]);
        }
      } catch (e) {
        console.warn('No se pudieron cargar componentes del activo', e);
        setAvailableComponents([]);
      }

      // Preferir endpoint específico del backend
      try {
        const tasksByWo = await apiClient.get<TaskRead[]>(`/tasks/workorder/${workOrderId}`);
        setTasks(tasksByWo || []);
        setTotal((tasksByWo || []).length);
      } catch {
        // Fallback: obtener todas y filtrar por workorder_id
        const allTasksResp = await taskService.getTasks();
        const all = (allTasksResp.success && allTasksResp.data ? allTasksResp.data : []) as TaskRead[];
        const filteredTasks = all.filter((t: TaskRead) => t.workorder_id === workOrderId);
        setTasks(filteredTasks);
        setTotal(filteredTasks.length);
      }
    } catch (err) {
      console.error('Error loading work order detail:', err);
      message.error('Error loading work order details');
    } finally {
      setLoading(false);
    }
  }, [workOrderId, workOrderService, userService, assetService, taskService, componentService]);

  useEffect(() => {
    if (!authLoading && !isAuthenticated) {
      router.push('/login');
      return;
    }
    if (isAuthenticated) {
      loadData();
    }
  }, [isAuthenticated, authLoading, router, loadData]);

  // maintenance plans logic removed

  const handleCreateTask = () => {
    setEditingTask(null);
    taskForm.resetFields();
    setTaskModalVisible(true);
  };

  const handleEditTask = (task: TaskRead) => {
    setEditingTask(task);
    taskForm.setFieldsValue({
      ...task,
      due_date: task.due_date ? dayjs(task.due_date) : null,
    });
    setTaskModalVisible(true);
  };

  const handleDeleteTask = async (taskId: number) => {
    try {
      await taskService.deleteTask(taskId.toString());
      message.success('Task deleted');
      await loadData();
    } catch (err) {
      console.error('Error deleting task:', err);
      message.error('Error deleting task');
    }
  };

  const openCompleteTask = (task: TaskRead) => {
    setCompletingTask(task);
    completeForm.resetFields();
    setComponentErrors({}); // Clear component errors
    setCompleteModalVisible(true);
  };

  // Función para verificar si todas las tareas están completadas
  const areAllTasksCompleted = useMemo(() => {
    if (tasks.length === 0) return false; // No se puede completar si no hay tareas
    return tasks.every(task => task.status === TaskStatus.COMPLETED);
  }, [tasks]);

  // Función para abrir modal de finalizar workorder
  const handleOpenCompleteWorkOrder = () => {
    if (!areAllTasksCompleted) {
      message.warning('All tasks must be completed before finalizing the work order');
      return;
    }
    
    setCompleteWorkOrderModalVisible(true);
  };

  // Función para finalizar workorder
  const handleCompleteWorkOrder = async () => {
    if (!workOrder) return;
    
    try {
      setSaving(true);
      // Obtener datos de mantenimiento del formulario
  const mValues = maintenanceForm.getFieldsValue();
  const payload: { maintenance_notes?: string } = {};
  if (mValues.maintenance_notes) payload.maintenance_notes = mValues.maintenance_notes;
  const result = await workOrderService.completeWorkOrder(workOrder.id, payload);
      console.log('Workorder completed result:', result);
      
      message.success('Work order completed successfully');
      setCompleteWorkOrderModalVisible(false);
      maintenanceForm.resetFields();
      
      // Forzar un reload completo de los datos
      await loadData();
      
      // Adicionalmente, forzar un nuevo fetch directo
      setTimeout(async () => {
        try {
          const freshData = await workOrderService.getWorkOrder(workOrder.id);
          if (freshData.success && freshData.data) {
            console.log('Fresh workorder data:', freshData.data);
            setWorkOrder(freshData.data);
          }
        } catch (e) {
          console.warn('Failed to refresh workorder data:', e);
        }
      }, 500);
      
    } catch (error: unknown) {
      console.error('Error completing work order:', error);
      if (error && typeof error === 'object' && 'response' in error) {
        const apiError = error as { response?: { data?: { detail?: string } } };
        if (apiError.response?.data?.detail) {
          message.error(`Error: ${apiError.response.data.detail}`);
        } else {
          message.error('Error completing work order');
        }
      } else {
        message.error('Error completing work order');
      }
    } finally {
  setSaving(false);
    }
  };

  const handleCompleteTask = async (values: { actual_hours?: number; notes?: string; description?: string; used_components?: { component_id: number; quantity: number }[] }) => {
    if (!completingTask) return;
    try {
      setSaving(true);
      setComponentErrors({}); // Clear previous errors
      await taskService.completeTask(String(completingTask.id), {
        actual_hours: values.actual_hours,
        notes: values.notes,
        description: values.description,
        used_components: (values.used_components || []).filter(u => u && u.component_id && u.quantity)
      });
      message.success('Task completed successfully');
      setCompleteModalVisible(false);
      setCompletingTask(null);
      completeForm.resetFields();
      await loadData();
    } catch (e: unknown) {
      console.error('Error completing task', e);
      
      // Handle specific inventory error
      const error = e as { response?: { status?: number; data?: { detail?: string } } };
      if (error?.response?.status === 400 && error?.response?.data?.detail?.includes('Insufficient inventory')) {
        const componentId = error.response.data.detail.match(/component (\d+)/)?.[1];
        const componentName = availableComponents.find(c => c.id === parseInt(componentId || '0'))?.name || `#${componentId}`;
        
        // Set error for specific component
        if (componentId) {
          setComponentErrors({ [parseInt(componentId)]: `Insufficient inventory for component: ${componentName}` });
        }
        message.error(`Insufficient inventory for component: ${componentName}`, 10);
      } else if (error?.response?.data?.detail) {
        message.error(`Error: ${error.response.data.detail}`, 8);
      } else {
        message.error('Could not complete task. Please verify the entered data.');
      }
    } finally {
      setSaving(false);
    }
  };

  const handleChangePage = (p: number, ps: number) => {
    setPage(p);
    setPageSize(ps);
    // Como las tareas se cargan todas de una vez, no necesitamos recargar
  };

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const handleTaskSubmit = async (values: Record<string, any>) => {
    if (!workOrder) return;
    try {
      const payload: TaskCreate | TaskUpdate = {
        title: values.title,
        description: values.description || '', // Asegurar que description no sea undefined
        status: values.status,
        priority: values.priority,
        assigned_to: values.assigned_to,
        estimated_hours: values.estimated_hours,
        due_date: values.due_date ? dayjs(values.due_date).toISOString() : undefined,
        workorder_id: workOrder.id,
      };
      // Parse used components JSON field if provided
      if (values.used_components_json) {
        try {
          const parsed = JSON.parse(values.used_components_json);
          if (Array.isArray(parsed)) {
            (payload as unknown as { used_components?: { component_id: number; quantity: number }[] }).used_components = parsed as { component_id: number; quantity: number }[];
          }
        } catch {
          message.warning('Invalid used components JSON, ignoring');
        }
      }
      if (editingTask) {
        await taskService.updateTask(editingTask.id.toString(), payload);
        message.success('Task updated');
      } else {
        await taskService.createTask(payload as TaskCreate);
        message.success('Task created');
      }
      setTaskModalVisible(false);
      taskForm.resetFields();
      await loadData();
    } catch (err) {
      console.error('Error saving task:', err);
      message.error('Error saving task');
    }
  };

  const taskColumns: ColumnsType<TaskRead> = [
    { 
      title: 'Title', 
      dataIndex: 'title', 
      key: 'title',
      render: (title: string, record: TaskRead) => (
        <span style={{ 
          opacity: record.status === TaskStatus.COMPLETED ? 0.5 : 1,
          textDecoration: record.status === TaskStatus.COMPLETED ? 'line-through' : 'none'
        }}>
          {record.status === TaskStatus.COMPLETED && (
            <CheckCircleOutlined style={{ color: '#52c41a', marginRight: 8 }} />
          )}
          {title}
        </span>
      )
    },
    {
      title: 'Status',
      dataIndex: 'status',
      key: 'status',
      render: (status: TaskStatus, record: TaskRead) => (
        <Tag 
          color={getTaskStatusColor(status as unknown as string)}
          style={{ 
            opacity: record.status === TaskStatus.COMPLETED ? 0.7 : 1
          }}
        >
          {formatLabel(status as unknown as string)}
        </Tag>
      ),
    },
    {
      title: 'Priority',
      dataIndex: 'priority',
      key: 'priority',
      render: (p: TaskPriority, record: TaskRead) => (
        <Tag 
          color={getSeverityColor(p as unknown as string)}
          style={{ 
            opacity: record.status === TaskStatus.COMPLETED ? 0.7 : 1
          }}
        >
          {formatLabel(p as unknown as string)}
        </Tag>
      ),
    },
    {
      title: 'Assigned To',
      dataIndex: 'assigned_to',
      key: 'assigned_to',
      render: (userId?: number, record?: TaskRead) => (
        <span style={{ 
          opacity: record?.status === TaskStatus.COMPLETED ? 0.5 : 1
        }}>
          <UserOutlined style={{ marginRight: 6 }} />
          {getUserName(userId)}
        </span>
      ),
    },
    {
      title: 'Due Date',
      dataIndex: 'due_date',
      key: 'due_date',
      render: (date?: string, record?: TaskRead) => (
        <span style={{ 
          opacity: record?.status === TaskStatus.COMPLETED ? 0.5 : 1
        }}>
          {date ? dayjs(date).format('DD/MM/YYYY') : '-'}
        </span>
      ),
    },
  ];

  if (authLoading || loading) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '50vh' }}>
        <Spin size="large" />
      </div>
    );
  }

  if (!isAuthenticated) return null;

  const tabs: TabDef[] = [
    {
      key: 'tasks',
      tab: <span><ToolOutlined /> Tasks ({tasks.length})</span>,
      content: (
        <EntityList<TaskRead>
          title="Work Order Tasks"
          data={tasks}
          columns={taskColumns}
          rowKey="id"
          loading={loading}
          createLabel={user?.role === 'Admin' || user?.role === 'Supervisor' ? 'Add New Task' : undefined}
          onCreate={(user?.role === 'Admin' || user?.role === 'Supervisor') ? handleCreateTask : undefined}
          onView={(t) => handleEditTask(t as TaskRead)}
          onDoubleClick={(t) => openCompleteTask(t as TaskRead)}
          onEdit={(user?.role === 'Admin' || user?.role === 'Supervisor') ? (t) => handleEditTask(t as TaskRead) : undefined}
          onDelete={(user?.role === 'Admin' || user?.role === 'Supervisor') ? (async (t) => handleDeleteTask((t as TaskRead).id)) : undefined}
          headerExtras={(selected) => {
            const t = selected as unknown as TaskRead | null;
            const canComplete = !!t && t.status !== TaskStatus.COMPLETED;
            return (
              <AppButton variant="primary" icon={<CheckCircleOutlined />} disabled={!canComplete} onClick={() => t && openCompleteTask(t)}>
              </AppButton>
            );
          }}
          scrollX={800}
          scrollY={'800px'}
          viewButtonLabel="Details"
          pagination={{ current: page, pageSize, total }}
          onChangePage={handleChangePage}
        />
      ),
    },
  ];

  return (
    <div className="overflow-hidden flex flex-col" style={{ padding: 24 }}>
      <DetailWithTabs
        backHref="/workorders"
        title={workOrder ? workOrder.title : 'Work Order'}
        descriptions={
          workOrder ? (
            <Descriptions bordered size="small" column={3}>
              <Descriptions.Item label="Type">{workOrder.work_type}</Descriptions.Item>
              <Descriptions.Item label="Asset">{getAssetName(workOrder.asset_id)}</Descriptions.Item>
              <Descriptions.Item label="Assigned To">{getUserName(workOrder.assigned_to)}</Descriptions.Item>
              <Descriptions.Item label="Scheduled Date">{workOrder.scheduled_date ? dayjs(workOrder.scheduled_date).format('YYYY-MM-DD') : 'N/A'}</Descriptions.Item>
              {(workOrder.status === 'COMPLETED' || workOrder.status === 'completed') ? (
                <>
                  <Descriptions.Item label="Actual Hours">{workOrder.actual_hours ? `${workOrder.actual_hours} hrs` : 'N/A'}</Descriptions.Item>
                  <Descriptions.Item label="Actual Cost">{workOrder.actual_cost ? `$${workOrder.actual_cost.toLocaleString()}` : 'N/A'}</Descriptions.Item>
                </>
              ) : (
                <>
                  <Descriptions.Item label="Estimated Hours">{workOrder.estimated_hours ?? 'N/A'}</Descriptions.Item>
                  <Descriptions.Item label="Estimated Cost">{workOrder.estimated_cost ? `$${workOrder.estimated_cost.toLocaleString()}` : 'N/A'}</Descriptions.Item>
                </>
              )}
              <Descriptions.Item label="Description" span={3}>{workOrder.description || 'N/A'}</Descriptions.Item>
            </Descriptions>
          ) : (
            <Text type="secondary">No work order data</Text>
          )
        }
        tabs={tabs}
        rightActions={workOrder && (
          <Space>
            <Tag color={getWorkOrderStatusColor(workOrder.status as unknown as string)}>{formatLabel(workOrder.status)}</Tag>
            <Tag color={getWorkOrderPriorityColor(workOrder.priority as unknown as string)}>{formatLabel(workOrder.priority)}</Tag>
            {workOrder.status !== 'COMPLETED' && workOrder.status !== 'completed' && (user?.role === 'Admin' || user?.role === 'Supervisor') && (
              <Button
                type="primary"
                icon={<CheckCircleOutlined />}
                onClick={handleOpenCompleteWorkOrder}
                disabled={!areAllTasksCompleted}
                style={{ backgroundColor: areAllTasksCompleted ? '#52c41a' : undefined }}
              >
                Complete Order
              </Button>
            )}
          </Space>
        )}
      />

      {/* Modal de crear/editar tarea usando ModalDialog */}
      <ModalDialog
        open={taskModalVisible}
        title={editingTask ? 'Edit Task' : 'Create New Task'}
        onClose={() => setTaskModalVisible(false)}
        width={600}
        primary={{ label: editingTask ? 'Update' : 'Create', onClick: () => taskForm.submit() }}
        secondary={{ label: 'Cancel', onClick: () => setTaskModalVisible(false) }}
      >
        <Form
          form={taskForm}
          onFinish={handleTaskSubmit}
          layout="vertical"
          initialValues={{
            status: TaskStatus.PENDING,
            priority: TaskPriority.MEDIUM,
          }}
        >
          <Form.Item name="title" label="Title" rules={[{ required: true, message: 'Please enter task title' }]}> 
            <Input placeholder="Enter task title" />
          </Form.Item>
          <Form.Item name="description" label="Description">
            <TextArea rows={3} placeholder="Enter task description" />
          </Form.Item>

          <Row gutter={16}>
            <Col span={12}>
              <Form.Item name="status" label="Status" rules={[{ required: true, message: 'Please select status' }]}> 
                <Select placeholder="Select status">
                  <Option value={TaskStatus.PENDING}>Pending</Option>
                  <Option value={TaskStatus.IN_PROGRESS}>In Progress</Option>
                  <Option value={TaskStatus.COMPLETED}>Completed</Option>
                  <Option value={TaskStatus.CANCELLED}>Cancelled</Option>
                </Select>
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="priority" label="Priority" rules={[{ required: true, message: 'Please select priority' }]}> 
                <Select placeholder="Select priority">
                  <Option value={TaskPriority.LOW}>Low</Option>
                  <Option value={TaskPriority.MEDIUM}>Medium</Option>
                  <Option value={TaskPriority.HIGH}>High</Option>
                  <Option value={TaskPriority.CRITICAL}>Critical</Option>
                </Select>
              </Form.Item>
            </Col>
          </Row>

          <Row gutter={16}>
            <Col span={12}>
              <Form.Item name="assigned_to" label="Assigned To">
                <Select allowClear placeholder="Select user">
                  {users.map(user => (
                    <Option key={user.id} value={user.id}>
                      {user.first_name} {user.last_name}
                    </Option>
                  ))}
                </Select>
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="due_date" label="Due Date">
                <Input type="date" />
              </Form.Item>
            </Col>
          </Row>

          <Row gutter={16}>
            <Col span={12}>
              <Form.Item name="estimated_hours" label="Estimated Hours">
                <InputNumber min={0} style={{ width: '100%' }} placeholder="0" />
              </Form.Item>
            </Col>
          </Row>
        </Form>
      </ModalDialog>

      {/* Modal para completar tarea usando ModalDialog con UI mejorada */}
      <ModalDialog
        open={completeModalVisible}
        title={
          <Space>
            <CheckCircleOutlined style={{ color: '#52c41a' }} />
            {completingTask ? `Complete Task: ${completingTask.title}` : 'Complete Task'}
          </Space>
        }
        onClose={() => setCompleteModalVisible(false)}
        width={800}
        primary={{ label: 'Complete Task', onClick: () => completeForm.submit(), loading: saving }}
        secondary={{ label: 'Cancel', onClick: () => setCompleteModalVisible(false) }}
      >
        <Form form={completeForm} layout="vertical" onFinish={handleCompleteTask}>
          {/* Información de la tarea */}
          {completingTask && (
            <Card size="small" style={{ marginBottom: 16, backgroundColor: '#f8f9fa' }}>
              <Row gutter={16}>
                <Col span={8}>
                  <Typography.Text strong>Current Status:</Typography.Text>
                  <br />
                  <Tag color={getTaskStatusColor(completingTask.status as unknown as string)}>
                    {formatLabel(completingTask.status as unknown as string)}
                  </Tag>
                </Col>
                <Col span={8}>
                  <Typography.Text strong>Priority:</Typography.Text>
                  <br />
                  <Tag color={getSeverityColor(completingTask.priority as unknown as string)}>
                    {formatLabel(completingTask.priority as unknown as string)}
                  </Tag>
                </Col>
                <Col span={8}>
                  <Typography.Text strong>Estimated Hours:</Typography.Text>
                  <br />
                  <Typography.Text>{completingTask.estimated_hours || 'Not specified'}</Typography.Text>
                </Col>
              </Row>
            </Card>
          )}

          {/* Detalles de finalización */}
          <Card title="Completion Details" size="small" style={{ marginBottom: 16 }}>
            <Row gutter={16}>
              <Col span={8}>
                <Form.Item 
                  name="actual_hours" 
                  label={
                    <Space>
                      <span>Actual Hours</span>
                      <Tooltip title="Actual time spent to complete the task">
                        <InfoCircleOutlined style={{ color: '#1890ff' }} />
                      </Tooltip>
                    </Space>
                  }
                >
                  <InputNumber 
                    min={0.1} 
                    step={0.5} 
                    style={{ width: '100%' }} 
                    placeholder="e.g. 2.5"
                    suffix="hrs"
                  />
                </Form.Item>
              </Col>
            </Row>
            
            <Form.Item name="notes" label="Closing Notes">
              <Input.TextArea 
                rows={3} 
                placeholder="Describe the work performed, problems encountered, observations..."
                showCount
                maxLength={500}
              />
            </Form.Item>
            
            <Form.Item name="description" label="Description Update (optional)">
              <Input.TextArea 
                rows={2} 
                placeholder="Update the task description if necessary"
                showCount
                maxLength={300}
              />
            </Form.Item>
          </Card>

          {/* Componentes utilizados */}
          <Form.List name="used_components">
            {(fields, { add, remove }) => (
              <Card 
                title={
                  <Space>
                    <ToolOutlined />
                    <span>Used Components</span>
                    <Typography.Text type="secondary">({fields.length})</Typography.Text>
                  </Space>
                }
                size="small"
                extra={
                  <Button 
                    type="dashed" 
                    icon={<PlusOutlined />} 
                    onClick={() => add()}
                    size="small"
                  >
                    Add Component
                  </Button>
                }
                style={{ marginBottom: 16 }}
              >
                {fields.length === 0 && (
                  <div style={{ textAlign: 'center', padding: '20px 0', color: '#8c8c8c' }}>
                    <ToolOutlined style={{ fontSize: '24px', marginBottom: '8px' }} />
                    <br />
                    <Typography.Text type="secondary">
                      No components have been added
                    </Typography.Text>
                    <br />
                    <Typography.Text type="secondary" style={{ fontSize: '12px' }}>
                      Click &quot;Add Component&quot; to register used materials
                    </Typography.Text>
                  </div>
                )}
                
                {fields.map((field, index) => (
                  <Card 
                    key={field.key} 
                    size="small" 
                    style={{ marginBottom: 8 }}
                    title={
                      <Space>
                        <Typography.Text strong>Component #{index + 1}</Typography.Text>
                      </Space>
                    }
                    extra={
                      <Tooltip title="Remove component">
                        <Button 
                          danger 
                          type="text" 
                          icon={<DeleteOutlined />}
                          onClick={() => remove(field.name)}
                          size="small"
                        />
                      </Tooltip>
                    }
                  >
                    <Row gutter={12} align="middle">
                      <Col span={14}>
                        <Form.Item 
                          {...field} 
                          name={[field.name, 'component_id']} 
                          label="Component"
                          rules={[{ required: true, message: 'Select a component' }]}
                          style={{ marginBottom: 0 }}
                          validateStatus={componentErrors[completeForm.getFieldValue(['used_components', field.name, 'component_id'])] ? 'error' : ''}
                          help={componentErrors[completeForm.getFieldValue(['used_components', field.name, 'component_id'])] || ''}
                        > 
                          <Select
                            showSearch
                            placeholder="Search and select component..."
                            optionFilterProp="children"
                            filterOption={(input, option) => {
                              const child = (option as { children?: React.ReactNode })?.children;
                              const label = typeof child === 'string' ? child : '';
                              return label.toLowerCase().includes(input.toLowerCase());
                            }}
                            size="small"
                          >
                            {availableComponents.map(c => (
                              <Option key={c.id} value={c.id}>
                                <Space>
                                  <ToolOutlined />
                                  {c.name}
                                </Space>
                              </Option>
                            ))}
                          </Select>
                        </Form.Item>
                      </Col>
                      <Col span={10}>
                        <Form.Item 
                          {...field} 
                          name={[field.name, 'quantity']} 
                          label="Quantity"
                          rules={[
                            { required: true, message: 'Enter quantity' },
                            { type: 'number', min: 0.1, message: 'Quantity must be greater than 0' }
                          ]}
                          style={{ marginBottom: 0 }}
                        > 
                          <InputNumber 
                            min={0.1} 
                            step={0.1} 
                            style={{ width: '100%' }} 
                            placeholder="Quantity"
                            precision={2}
                            size="small"
                          />
                        </Form.Item>
                      </Col>
                    </Row>
                  </Card>
                ))}
                
                {fields.length > 0 && (
                  <Divider style={{ margin: '12px 0' }}>
                    <Typography.Text type="secondary" style={{ fontSize: '12px' }}>
                      {fields.length} component{fields.length !== 1 ? 's' : ''} registered
                    </Typography.Text>
                  </Divider>
                )}
              </Card>
            )}
          </Form.List>
        </Form>
      </ModalDialog>

      {/* Modal para finalizar workorder */}
      <ModalDialog
        open={completeWorkOrderModalVisible}
        title={
          <Space>
            <CheckCircleOutlined style={{ color: '#52c41a' }} />
            Complete Work Order
          </Space>
        }
        onClose={() => setCompleteWorkOrderModalVisible(false)}
        width={600}
        primary={{ 
          label: 'Complete Order', 
          onClick: handleCompleteWorkOrder, 
          loading: saving
        }}
        secondary={{ 
          label: 'Cancel', 
          onClick: () => setCompleteWorkOrderModalVisible(false)
        }}
      >
        {/* Información de la workorder */}
        {workOrder && (
          <Card size="small" style={{ marginBottom: 16, backgroundColor: '#f6ffed', border: '1px solid #b7eb8f' }}>
            <Row gutter={16}>
              <Col span={8}>
                <Typography.Text strong>Current Status:</Typography.Text>
                <br />
                <Tag color={getWorkOrderStatusColor(workOrder.status as unknown as string)}>
                  {formatLabel(workOrder.status)}
                </Tag>
              </Col>
              <Col span={8}>
                <Typography.Text strong>Priority:</Typography.Text>
                <br />
                <Tag color={getWorkOrderPriorityColor(workOrder.priority as unknown as string)}>
                  {formatLabel(workOrder.priority)}
                </Tag>
              </Col>
              <Col span={8}>
                <Typography.Text strong>Completed Tasks:</Typography.Text>
                <br />
                <Typography.Text style={{ color: '#52c41a', fontWeight: 'bold' }}>
                  {tasks.filter(t => t.status === TaskStatus.COMPLETED).length} / {tasks.length}
                </Typography.Text>
              </Col>
            </Row>
          </Card>
        )}

        {/* Resumen de cálculos automáticos */}
        <Card title="Automatic Calculations" size="small" style={{ marginBottom: 16 }}>
          <Row gutter={16}>
            <Col span={12}>
              <Typography.Text strong>Total Hours:</Typography.Text>
              <br />
              <Typography.Text style={{ fontSize: '16px', color: '#1890ff' }}>
                {tasks.reduce((sum, task) => sum + (task.actual_hours || 0), 0).toFixed(1)} hours
              </Typography.Text>
              <br />
              <Typography.Text type="secondary" style={{ fontSize: '12px' }}>
                Sum of actual hours from all completed tasks
              </Typography.Text>
            </Col>
            <Col span={12}>
              <Typography.Text strong>Estimated Cost:</Typography.Text>
              <br />
              <Typography.Text style={{ fontSize: '16px', color: '#52c41a' }}>
                ${(() => {
                  const totalHours = tasks.reduce((sum, task) => sum + (task.actual_hours || 0), 0);
                  if (workOrder?.estimated_cost && workOrder?.estimated_hours) {
                    const hourlyRate = workOrder.estimated_cost / workOrder.estimated_hours;
                    return (totalHours * hourlyRate).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 });
                  }
                  return (totalHours * 50).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 });
                })()}
              </Typography.Text>
              <br />
              <Typography.Text type="secondary" style={{ fontSize: '12px' }}>
                Automatically calculated based on hours worked
              </Typography.Text>
            </Col>
          </Row>
        </Card>

        {/* Notas opcionales para registro Maintenance */}
        <Card title="Maintenance Notes (optional)" size="small" style={{ marginBottom: 16 }}>
          <Form form={maintenanceForm} layout="vertical">
            <Form.Item name="maintenance_notes" label="Notes">
              <Input.TextArea rows={3} placeholder="Maintenance notes" maxLength={500} showCount />
            </Form.Item>
            <Typography.Text type="secondary" style={{ fontSize: 12 }}>
              If you add notes a maintenance record will be generated automatically (type inferred).
            </Typography.Text>
          </Form>
        </Card>

        {/* Información importante */}
  <Card size="small" style={{ backgroundColor: '#f0f9ff', border: '1px solid #bae7ff' }}>
          <Typography.Text type="secondary" style={{ fontSize: '12px' }}>
            <InfoCircleOutlined style={{ marginRight: 4 }} />
            When completing this work order, it will be marked as completed and the total hours and costs 
            will be automatically calculated based on the completed tasks. This action cannot be undone.
          </Typography.Text>
        </Card>
      </ModalDialog>
    </div>
  );
}
