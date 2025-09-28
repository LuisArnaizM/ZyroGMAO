'use client';

import React, { useEffect, useState, useCallback } from 'react';
import dayjs from 'dayjs';
import { plannerService, PlannerWeek, PlannerUserRow, PlannerTask } from '../services/planner.service';
import { TaskService } from '../services/task.service';
import { WorkOrderService } from '../services/workorder.service';
import { WorkOrderRead } from '../types';
import { TaskRead } from '../types';
import { apiClient } from '../utils/api-client';
import { Input, Form, InputNumber, Select, message, Tooltip, Dropdown } from 'antd';
import ModalDialog from '../components/ui/ModalDialog';
import { ApiError } from '../utils/api-client';
import { LeftOutlined, RightOutlined, CalendarOutlined, ClockCircleOutlined, PieChartOutlined } from '@ant-design/icons';
import { AppButton } from '../components/ui/AppButton';
import Link from 'next/link';
import { ManagementPageLayout } from '../components/layout/ManagementPageLayout';
import { TaskPriority } from '../types';

const DEFAULT_WORKDAY_HOURS = 8; // fallback
const COLORS = ['#1677ff','#722ed1','#eb2f96','#fa8c16','#13c2c2','#52c41a','#fa541c','#2f54eb'];

interface NewTaskFormValues {
  title: string;
  estimated_hours?: number;
  due_date: dayjs.Dayjs; // almacenado como Dayjs en formulario
  assigned_to: number;
  priority?: TaskPriority;
}

export default function PlannerPage() {
  const [week, setWeek] = useState<PlannerWeek | null>(null);
  const [monday, setMonday] = useState(dayjs().startOf('week').add(1,'day')); // Monday start
  const [loading, setLoading] = useState(false);
  const [showModal, setShowModal] = useState(false);
  const [selectedUserId, setSelectedUserId] = useState<number | null>(null);
  const [selectedDate, setSelectedDate] = useState<string | null>(null);
  const [selectedMaxHours, setSelectedMaxHours] = useState<number | null>(null);
  const [form] = Form.useForm<NewTaskFormValues>();
  const taskService = React.useMemo(() => new TaskService(apiClient), []);
  const workOrderService = React.useMemo(() => new WorkOrderService(apiClient), []);

  const [workOrders, setWorkOrders] = useState<WorkOrderRead[]>([]);
  const [selectedWorkOrderId, setSelectedWorkOrderId] = useState<number | null>(null);
  const [workOrderTasks, setWorkOrderTasks] = useState<TaskRead[]>([]);
  const [selectedTemplateTaskId, setSelectedTemplateTaskId] = useState<number | null>(null);
  const [editingTask, setEditingTask] = useState<TaskRead | null>(null);
  const [selectedCell, setSelectedCell] = useState<{ userId: number; date: string } | null>(null);
  const [selectedTaskId, setSelectedTaskId] = useState<number | null>(null);

  const loadWeek = useCallback(async () => {
    try {
      setLoading(true);
      const data = await plannerService.getWeek({ start: monday.format('YYYY-MM-DD'), days: 7 });
      setWeek(data);
    } catch (e) {
      console.error(e); message.error('Error cargando planner');
    } finally { setLoading(false); }
  }, [monday]);

  useEffect(()=> { loadWeek(); }, [loadWeek]);

  // Cuando se abre el modal, cargar lista de workorders (primera page)
  useEffect(() => {
    if (showModal) {
      (async () => {
        try {
          const res = await workOrderService.getWorkOrders({ pagination: { page: 1, page_size: 50 } });
          if (res.success) setWorkOrders(res.data || []);
        } catch (err) {
          console.error('Error loading workorders', err);
        }
      })();
    } else {
      setWorkOrders([]);
      setSelectedWorkOrderId(null);
      setWorkOrderTasks([]);
    }
  }, [showModal, workOrderService]);

  const openCreateTask = (userId: number, date: string) => {
    setSelectedUserId(userId);
    setSelectedDate(date);
    // calcular horas restantes de la jornada: use capacity_hours si está, si no fallback a DEFAULT_WORKDAY_HOURS
    let remaining = DEFAULT_WORKDAY_HOURS;
    try {
      const u = week?.users.find(x => x.user.id === userId);
      const d = u?.days.find(dd => dd.date === date);
      const capacity = d?.capacity_hours ?? DEFAULT_WORKDAY_HOURS;
      const planned = d?.planned_hours ?? 0;
      remaining = Math.max(0, Number((capacity - planned).toFixed(1)));
    } catch {
      // fallback: keep DEFAULT_WORKDAY_HOURS
    }
    setSelectedMaxHours(remaining);
    // abrir modal; rellenado real del formulario se hace en useEffect cuando el modal está montado
    setEditingTask(null);
    setShowModal(true);
  };

  // (removed overload) openEditTask implemented further below using TaskRead

  // Cuando el modal se abre, asegurar que el formulario reciba los valores (date pickers montados)
  useEffect(() => {
    if (showModal && selectedDate) {
      form.resetFields();
      if (!editingTask) {
        // creating: prefill with selectedDate and remaining hours
        form.setFieldsValue({ due_date: dayjs(selectedDate), estimated_hours: selectedMaxHours ?? undefined });
      } else {
        // editing: keep the task's own estimated_hours (openEditTask already set form fields)
        form.setFieldsValue({ due_date: dayjs(selectedDate) });
      }
    }
  }, [showModal, selectedDate, selectedMaxHours, form, editingTask]);
  
  const handleCloseModal = () => {
    setShowModal(false);
    setSelectedUserId(null);
    setSelectedDate(null);
    setSelectedMaxHours(null);
    form.resetFields();
    setWorkOrders([]);
    setSelectedWorkOrderId(null);
    setWorkOrderTasks([]);
    setSelectedTemplateTaskId(null);
  };

  const handlePrevWeek = () => setMonday(m=> m.subtract(7,'day'));
  const handleNextWeek = () => setMonday(m=> m.add(7,'day'));
  const handleToday = () => setMonday(dayjs().startOf('week').add(1,'day'));

  const usedColors = new Map<number,string>();
  const colorForTask = (id:number) => { if(!usedColors.has(id)) { usedColors.set(id, COLORS[usedColors.size % COLORS.length]); } return usedColors.get(id)!; };

  const submitTask = async () => {
    try {
      const values = form.getFieldsValue();
      if(!selectedUserId || !selectedDate) return;
      const payloadCreate: import('../types').TaskCreate = {
        title: String(values.title || ''),
        estimated_hours: values.estimated_hours ?? undefined,
        assigned_to: selectedUserId,
        priority: values.priority || TaskPriority.MEDIUM,
        due_date: selectedDate,
        workorder_id: selectedWorkOrderId ?? undefined,
      };

      const payloadUpdate: import('../types').TaskUpdate = {
        title: String(values.title || ''),
        estimated_hours: values.estimated_hours ?? undefined,
        assigned_to: selectedUserId,
        priority: values.priority || TaskPriority.MEDIUM,
        // do not change due_date on update unless desired; keep it as is
      };

      if (!editingTask) {
        await taskService.createTask(payloadCreate);
        message.success('Tarea creada');
      } else {
        await taskService.updateTask(String(editingTask.id), payloadUpdate);
        message.success('Tarea actualizada');
      }
      setShowModal(false);
      await loadWeek();
      // limpiar estado del modal
      setSelectedUserId(null);
      setSelectedDate(null);
      setSelectedMaxHours(null);
      setSelectedWorkOrderId(null);
      setWorkOrderTasks([]);
      setEditingTask(null);
      form.resetFields();
    } catch(e: unknown) {
      console.error(e);
      if (e instanceof ApiError) {
        const data = e.data as unknown;
        let detail: string | null = null;
        if (data && typeof data === 'object') {
          const drec = data as Record<string, unknown>;
          if (typeof drec['detail'] === 'string') detail = drec['detail'] as string;
          else if (typeof drec['message'] === 'string') detail = drec['message'] as string;
        } else if (typeof data === 'string') {
          detail = data;
        }
        console.error('API Error creating task:', e.status, e.message, e.data);
        message.error(detail || `Error ${e.status}: ${e.message}`);
      } else if (e instanceof Error) {
        console.error(e);
        message.error(e.message || 'Error creando tarea');
      } else {
        console.error('Unknown error', e);
        message.error('Error creando tarea');
      }
    }
  };

  const deleteTask = async (taskId: number) => {
    try {
      await taskService.deleteTask(String(taskId));
      message.success('Tarea eliminada');
      await loadWeek();
      if (editingTask && editingTask.id === taskId) {
        setEditingTask(null);
        handleCloseModal();
      }
    } catch (err) {
      console.error('Error deleting task', err);
      message.error('Error eliminando tarea');
    }
  };

  const openEditTask = async (t: PlannerTask) => {
    try {
      const res = await taskService.getTask(String(t.id));
      if (!res.success) throw new Error('Error cargando tarea');
  if (!res.data) throw new Error('Tarea no encontrada');
  const full: TaskRead = res.data as TaskRead;
  setEditingTask(full);
  setSelectedUserId(full.assigned_to ?? null);
  setSelectedDate(full.due_date ?? null);

      try {
        const u = week?.users.find(x => x.user.id === (full.assigned_to ?? -1));
        const d = u?.days.find(dd => dd.date === (full.due_date ?? ''));
        const capacity = d?.capacity_hours ?? DEFAULT_WORKDAY_HOURS;
        const planned = d?.planned_hours ?? 0;
        const remaining = Math.max(0, Number((capacity - (planned - (full.estimated_hours || 0))).toFixed(1)));
        setSelectedMaxHours(remaining);
      } catch {
        setSelectedMaxHours(DEFAULT_WORKDAY_HOURS);
      }

      if (full.workorder_id) {
        setSelectedWorkOrderId(full.workorder_id);
        try {
          const res2 = await taskService.getTasksByWorkOrder(String(full.workorder_id));
          if (res2.success) setWorkOrderTasks(res2.data || []);
        } catch (err) { console.error(err); }
      } else {
        setSelectedWorkOrderId(null);
        setWorkOrderTasks([]);
      }

      form.resetFields();
      form.setFieldsValue({ title: full.title, estimated_hours: full.estimated_hours, priority: full.priority });
      setShowModal(true);
    } catch (err) {
      console.error('Error opening edit task', err);
      message.error('Error cargando tarea');
    }
  };

  const onWorkOrderSelect = async (woId: number) => {
    setSelectedWorkOrderId(woId);
    try {
      const res = await taskService.getTasksByWorkOrder(String(woId));
      if (res.success) setWorkOrderTasks(res.data || []);
    } catch (err) {
      console.error('Error loading tasks for workorder', err);
    }
  };

  const totalCapacityRaw = week?.users.reduce((acc,u)=> acc + u.days.reduce((a,d)=> a + d.capacity_hours,0), 0) || 0;
  const totalPlannedRaw = week?.users.reduce((acc,u)=> acc + u.days.reduce((a,d)=> a + d.planned_hours,0),0) || 0;
  const totalCapacity = Math.round(totalCapacityRaw * 10)/10;
  const totalPlanned = Math.round(totalPlannedRaw * 10)/10;
  const utilization = totalCapacity? ((totalPlanned/totalCapacity)*100):0;
  const nonWorkingDays = week?.users.reduce((acc,u)=> acc + u.days.filter(d=> d.is_non_working || d.capacity_hours===0).length,0) || 0;

  return (
    <ManagementPageLayout
      kpis={[
        { title:'Capacidad (h)', value: totalCapacity, prefix:<ClockCircleOutlined /> },
        { title:'Planificado (h)', value: totalPlanned, prefix:<PieChartOutlined style={{color:'#1677ff'}} /> },
        { title:'Utilización (%)', value: Number(utilization.toFixed(0)), prefix:<PieChartOutlined style={{color: utilization>90? '#fa541c': utilization>75? '#fa8c16':'#52c41a'}} />, valueStyle:{ color: utilization>90? '#fa541c': utilization>75? '#fa8c16':'#52c41a' } },
        { title:'No Laborables', value: nonWorkingDays }
      ]}
      headerActions={null}
    >
      <div className="planner-wrapper" data-loading={loading}>
        <div className="flex items-center justify-between mb-4 relative gap-4">
          <div className="primary-gradient-dark rounded-xl text-primary px-5 py-2 shadow-lg title-card flex items-center gap-3">
            <h2 className="text-primary font-bold m-0 tracking-wide">Planner Semana {monday.format('DD/MM/YYYY')}</h2>
          </div>
          <div className="flex items-center gap-2 ml-auto">
            <Tooltip title="Calendario de disponibilidad">
              <Link href="/planner/calendar">
                <AppButton variant="primary" size="sm" icon={<CalendarOutlined />}>Calendario</AppButton>
              </Link>
            </Tooltip>
            <AppButton variant="ghost" size="sm" icon={<LeftOutlined />} onClick={handlePrevWeek}>Anterior</AppButton>
            <AppButton variant="primary" size="sm" onClick={handleToday}>Hoy</AppButton>
            <AppButton variant="ghost" size="sm" icon={<RightOutlined />} iconRight={null} onClick={handleNextWeek}>Siguiente</AppButton>
          </div>
        </div>
        <div className="planner-scroll">
          <table className="planner-table elegant-table">
            <thead>
              <tr>
                <th className="planner-user-cell p-2">Usuario</th>
                {week && [...Array(week.days).keys()].map(i=> {
                  const d = dayjs(week.start).add(i,'day');
                  const isToday = d.isSame(dayjs(),'day');
                  return <th key={i} className={`p-2 text-center planner-th ${isToday?'planner-th-today':''}`}>{d.format('ddd DD/MM')}</th>; })}
              </tr>
            </thead>
            <tbody>
              {week?.users.map((u: PlannerUserRow) => (
                <tr key={u.user.id}>
                  <td className="planner-user-cell p-2 whitespace-nowrap text-sm">
                    <span className="font-semibold">{u.user.first_name} {u.user.last_name}</span>
                  </td>
                  {u.days.map(day => {
                    const denom = day.capacity_hours || DEFAULT_WORKDAY_HOURS;
                    const freePct = denom>0 ? ((day.free_hours / denom) * 100) : 0;
                    const nonWorking = day.is_non_working || day.capacity_hours === 0;
                    const cellSelected = selectedCell?.userId === u.user.id && selectedCell?.date === day.date;
                    return (
                      <td key={day.date} className={`planner-day-cell align-top p-1 ${nonWorking?'planner-nonworking-cell':''} ${cellSelected ? 'selected' : ''}`} onClick={() => { setSelectedCell({ userId: u.user.id, date: day.date }); setSelectedTaskId(null); }}>
                        <div className={`planner-day-block ${nonWorking?'planner-nonworking-block':''}`}>
                          <div className="planner-cell-actions">
                            <button className="planner-cell-action-btn" onClick={(e)=>{ e.stopPropagation(); openCreateTask(u.user.id, day.date); }} title="Crear">+</button>
                            {day.tasks.length <= 1 ? (
                              <>
                                <button className="planner-cell-action-btn" onClick={(e)=>{ e.stopPropagation(); if(day.tasks.length>0){ const t = day.tasks[0]; setSelectedTaskId(t.id); openEditTask(t); } }} disabled={day.tasks.length===0} title="Editar">✎</button>
                                <button className="planner-cell-action-btn" onClick={(e)=>{ e.stopPropagation(); if(day.tasks.length>0){ const t = day.tasks[0]; deleteTask(t.id); } }} disabled={day.tasks.length===0} title="Borrar">🗑</button>
                              </>
                            ) : (
                              <Dropdown
                                menu={{
                                  items: day.tasks.map(t => ({ key: String(t.id), label: `${t.title} (${(t.estimated_hours||0).toFixed(1)}h)` })),
                                  onClick: ({ key }) => {
                                    const id = Number(key);
                                    const selected = day.tasks.find(tt => tt.id === id);
                                    if (selected) {
                                      setSelectedTaskId(selected.id);
                                      openEditTask(selected);
                                    }
                                  }
                                }}
                                trigger={['click']}
                              >
                                <button className="planner-cell-action-btn">✎</button>
                              </Dropdown>
                            )}
                            {day.tasks.length <= 1 ? null : (
                              <Dropdown
                                menu={{
                                  items: day.tasks.map(t => ({ key: `del-${t.id}`, label: `Borrar: ${t.title}` })),
                                  onClick: ({ key }) => {
                                    const idStr = String(key).replace(/^del-/, '');
                                    const id = Number(idStr);
                                    const selected = day.tasks.find(tt => tt.id === id);
                                    if (selected) deleteTask(selected.id);
                                  }
                                }}
                                trigger={['click']}
                              >
                                <button className="planner-cell-action-btn">🗑</button>
                              </Dropdown>
                            )}
                          </div>
                          <div className="flex h-full w-full">
                            {day.tasks.map(t=> {
                              const pct = denom>0 ? ((t.estimated_hours || 0)/denom)*100 : 100/Math.max(1, day.tasks.length);
                              const isSelected = selectedTaskId === t.id;
                              return (
                                <Tooltip key={t.id} title={`${t.title} (${(t.estimated_hours||0).toFixed(1)}h)`}>
                                  <div style={{ width:`${pct}%`, background: colorForTask(t.id), opacity: nonWorking? .5:1, position:'relative' }} className={`planner-task-bar ${isSelected? 'selected':''}`}>
                                    <span style={{cursor:'pointer'}} onClick={(e)=>{ e.stopPropagation(); setSelectedTaskId(t.id); setSelectedCell({ userId: u.user.id, date: day.date }); openEditTask(t); }}>{(t.estimated_hours||0).toFixed(1)}h</span>
                                  </div>
                                </Tooltip>
                              );
                            })}
                            {(!nonWorking && day.free_hours>0) && <div style={{ width:`${freePct}%`}} className="planner-free-bar">{day.free_hours.toFixed(1)}h</div>}
                            {nonWorking && day.tasks.length===0 && (
                              <div className="planner-nonworking-overlay">{day.reason || 'No laborable'}</div>
                            )}
                          </div>
                          {/* Botón flotante de añadir eliminado; las acciones (+, editar, borrar) se muestran al hacer hover en la celda */}
                        </div>
                        <div className="planner-day-meta">{day.planned_hours.toFixed(1)}/{denom.toFixed(1)}h{nonWorking && ' (NL)'}</div>
                      </td>
                    );
                  })}
                </tr>
              ))}
              {(!week || week.users.length===0) && <tr><td colSpan={8} className="text-center p-6 text-sm text-gray-500">No hay usuarios subordinados o sin datos.</td></tr>}
            </tbody>
          </table>
        </div>
      </div>

      <ModalDialog open={showModal} onClose={handleCloseModal} primary={{ label: 'Guardar', onClick: submitTask }} title={editingTask ? `Editar tarea — ${editingTask.title}` : 'Crear tarea'}>
        <Form form={form} layout="vertical" initialValues={{ priority: TaskPriority.MEDIUM }}>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <Form.Item label="Orden de trabajo">
                <Select
                  showSearch
                  allowClear
                  placeholder="Buscar workorder por id o título"
                  optionFilterProp="children"
                  value={selectedWorkOrderId ?? undefined}
                  onChange={async (val) => {
                    const id = val == null ? null : Number(val);
                    setSelectedTemplateTaskId(null);
                    if (id === null) {
                      setSelectedWorkOrderId(null);
                      setWorkOrderTasks([]);
                      return;
                    }
                    await onWorkOrderSelect(id);
                  }}
                  filterOption={(input, option) => {
                    const text = String(option?.children || '').toLowerCase();
                    return text.includes(String(input).toLowerCase());
                  }}
                >
                  {workOrders.map(wo => (
                    <Select.Option key={wo.id} value={wo.id}>{`#${wo.id} - ${wo.title}`}</Select.Option>
                  ))}
                </Select>
              </Form.Item>

              <Form.Item label="Tarea de la orden (plantilla)">
                <Select
                  showSearch
                  allowClear
                  placeholder={selectedWorkOrderId ? 'Selecciona una tarea de la OT' : 'Selecciona primero una OT'}
                  disabled={!selectedWorkOrderId}
                  value={selectedTemplateTaskId ?? undefined}
                  onChange={(val) => {
                    const id = val == null ? null : Number(val);
                    setSelectedTemplateTaskId(id);
                    if (id != null) {
                      const t = workOrderTasks.find(x => x.id === id);
                      if (t) form.setFieldsValue({ title: t.title, estimated_hours: t.estimated_hours });
                    }
                  }}
                  optionFilterProp="children"
                  filterOption={(input, option) => {
                    const text = String(option?.children || '').toLowerCase();
                    return text.includes(String(input).toLowerCase());
                  }}
                >
                  {workOrderTasks.map(t => (
                    <Select.Option key={t.id} value={t.id}>{`${t.title} ${t.estimated_hours ? `(${t.estimated_hours}h)` : ''}`}</Select.Option>
                  ))}
                </Select>
                <div className="mt-2 flex gap-2">
                  <AppButton size="sm" variant="primary" onClick={() => {
                    setSelectedTemplateTaskId(null);
                    form.setFieldsValue({ title: '', estimated_hours: selectedMaxHours ?? undefined });
                  }}>Crear nueva tarea</AppButton>
                  <div className="text-sm text-muted flex-1 self-center">La tarea se creará asignada al usuario y fecha pulsados en la matriz.</div>
                </div>
              </Form.Item>
            </div>

            <div>
              <Form.Item name="title" label="Título" rules={[{ required:true, message:'Obligatorio'}]}>
                <Input />
              </Form.Item>
              <Form.Item name="estimated_hours" label="Horas estimadas">
                <InputNumber min={0} max={selectedMaxHours ?? DEFAULT_WORKDAY_HOURS} style={{width:'100%'}} />
              </Form.Item>
              <Form.Item name="priority" label="Prioridad">
                <Select>
                  <Select.Option value={TaskPriority.LOW}>Baja</Select.Option>
                  <Select.Option value={TaskPriority.MEDIUM}>Media</Select.Option>
                  <Select.Option value={TaskPriority.HIGH}>Alta</Select.Option>
                  <Select.Option value={TaskPriority.CRITICAL}>Crítica</Select.Option>
                </Select>
              </Form.Item>
            </div>
          </div>
        </Form>
      </ModalDialog>
    </ManagementPageLayout>
  );
}
