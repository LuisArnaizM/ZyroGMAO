'use client';
import React, { useEffect, useState, useCallback } from 'react';
import dayjs from 'dayjs';
import { calendarService, WorkingDayPattern, SpecialDay } from '../../services/calendar.service';
import { userService } from '../../services/user.service';
import { ManagementPageLayout } from '../../components/layout/ManagementPageLayout';
import { Button as AntButton, Table, InputNumber, Switch, DatePicker, Form, Input, message, Select, Tag, Tabs } from 'antd';
import ModalDialog from '../../components/ui/ModalDialog';
import { PlusOutlined, ReloadOutlined, LeftOutlined, RightOutlined, CalendarOutlined, RestOutlined, UserOutlined, ClockCircleOutlined } from '@ant-design/icons';
import { AppButton } from '../../components/ui/AppButton';
import { useAuth } from '../../hooks/useAuth';

interface UserOption { id:number; name:string; }

const weekdayLabels = ['Mon','Tue','Wed','Thu','Fri','Sat','Sun'];

export default function CalendarManagementPage() {
  const { user: authUser } = useAuth();
  const [selectedUser, setSelectedUser] = useState<number | null>(null);
  const [users, setUsers] = useState<UserOption[]>([]);
  const [pattern, setPattern] = useState<WorkingDayPattern[]>([]);
  const [loadingPattern, setLoadingPattern] = useState(false);
  const [rangeStart, setRangeStart] = useState(dayjs().startOf('year'));
  const [rangeEnd, setRangeEnd] = useState(dayjs().endOf('year'));
  const [specialDays, setSpecialDays] = useState<SpecialDay[]>([]);
  // Vacaciones se derivan de specialDays con motivo 'Vacaciones'
  const [specialModalOpen, setSpecialModalOpen] = useState(false);
  const [vacationModalOpen, setVacationModalOpen] = useState(false);
  const [specialForm] = Form.useForm();
  const [vacForm] = Form.useForm();
  const [weekRef, setWeekRef] = useState(dayjs().startOf('week').add(1,'day'));
  const weekStart = weekRef.startOf('week').add(1,'day');
  const weekEnd = weekStart.add(6,'day');

  const kpiData = () => {
    const isVacation = (r?: string | null) => {
      const rr = (r || '').toLowerCase();
      return rr.includes('vac') || rr.includes('vaca');
    };
    const vacationsUser = specialDays.filter(d=> !d.is_working && isVacation(d.reason));
    const nonWorkingOther = specialDays.filter(d=> !d.is_working && !isVacation(d.reason));
    const totalWeeklyHours = pattern.filter(p=> p.is_active).reduce((acc,p)=> acc + (p.hours||0),0);
    const selectedUserName = selectedUser ? users.find(u=> u.id===selectedUser)?.name || selectedUser : '-';
    return [
      { title:'Vacations', value: vacationsUser.length, prefix:<RestOutlined />, color:'#ef4444' },
      { title:'Non‑working', value: nonWorkingOther.length, prefix:<CalendarOutlined />, color:'#f59e0b' },
      { title:'Weekly hours', value: totalWeeklyHours, prefix:<ClockCircleOutlined />, color:'#10b981' },
      { title:'User', value: selectedUserName, prefix:<UserOutlined />, color:'#6366f1' },
    ];
  };

  const prevWeek = ()=> { setWeekRef(w=> w.subtract(7,'day')); };
  const nextWeek = ()=> { setWeekRef(w=> w.add(7,'day')); };
  const thisWeek = ()=> { setWeekRef(dayjs().startOf('week').add(1,'day')); };

  const loadUsers = useCallback(async ()=>{
    try {
      if (authUser?.role === 'Tecnico') {
        const nameFromParts = `${authUser.first_name ?? ''} ${authUser.last_name ?? ''}`.trim();
        const displayName = authUser.full_name ?? (nameFromParts || authUser.username || 'Yo');
        const self: UserOption = { id: authUser.id, name: displayName };
        setUsers([self]);
        setSelectedUser(self.id);
        return;
      }
      const list = await userService.getAll();
      setUsers(list.map(u=> ({ id:u.id, name: `${u.first_name} ${u.last_name}` })));
      if(list.length>0 && !selectedUser) {
        setSelectedUser(list[0].id);
      }
    } catch(e){
      if (authUser) {
        const nameFromParts = `${authUser.first_name ?? ''} ${authUser.last_name ?? ''}`.trim();
        const displayName = authUser.full_name ?? (nameFromParts || authUser.username || 'Yo');
        const self: UserOption = { id: authUser.id, name: displayName };
        setUsers([self]);
        setSelectedUser(self.id);
      } else {
        console.error(e);
      }
    }
  },[authUser, selectedUser]);

  const loadPattern = useCallback(async ()=> {
    if(!selectedUser) return;
    setLoadingPattern(true);
    try {
      const p = await calendarService.getPattern(selectedUser);
      setPattern(p);
  } catch { message.error('Failed to load pattern'); }
    finally { setLoadingPattern(false); }
  }, [selectedUser]);

  const loadSpecials = useCallback(async ()=> {
    if(!selectedUser) return;
    try {
      const s = await calendarService.listSpecial(selectedUser, rangeStart.format('YYYY-MM-DD'), rangeEnd.format('YYYY-MM-DD'));
      setSpecialDays(s);
  } catch(e){ console.error(e); }
  }, [selectedUser, rangeStart, rangeEnd]);

  useEffect(()=> { loadUsers(); }, [loadUsers]);
  useEffect(()=> { loadPattern(); loadSpecials(); }, [loadPattern, loadSpecials]);

  // initPatternIfEmpty eliminado (ya no se usa)

  const updatePatternField = (weekday:number, field:'hours'|'is_active', value:number|boolean|undefined|null) => {
    setPattern(p=> p.map(r=> r.weekday===weekday? { ...r, [field]: value }: r));
  };

  const savePattern = async () => {
    if(!selectedUser) return;
    try {
      await calendarService.updatePattern(selectedUser, pattern);
      message.success('Patrón guardado');
      loadPattern();
    } catch { message.error('Error guardando patrón'); }
  };

  const openSpecialModal = () => {
    specialForm.resetFields();
    // Preseleccionar hoy para evitar confusión de campo vacío
    specialForm.setFieldsValue({ date: dayjs(), is_working: false });
    setSpecialModalOpen(true);
  };
  const openVacationModal = () => { vacForm.resetFields(); vacForm.setFieldsValue({ reason:'Vacations' }); setVacationModalOpen(true); };

  const submitSpecial = async () => {
    if(!selectedUser) return;
    try {
      await specialForm.validateFields();
      const vals = specialForm.getFieldsValue();
      await calendarService.addSpecial(selectedUser, { date: vals.date.format('YYYY-MM-DD'), is_working: vals.is_working, hours: vals.hours ?? null, reason: vals.reason || null });
      message.success('Saved');
      setSpecialModalOpen(false);
      loadSpecials();
    } catch (err) {
      console.error('Failed to save special day', err);
      message.error('Failed to save special day');
    }
  };

  const submitVacationRange = async () => {
    if(!selectedUser) return;
    try {
      const vals = vacForm.getFieldsValue();
      const start = vals.range[0].format('YYYY-MM-DD');
      const end = vals.range[1].format('YYYY-MM-DD');
      await calendarService.addVacationRange(selectedUser, { start_date:start, end_date:end, reason: vals.reason });
      message.success('Vacations added');
      setVacationModalOpen(false);
  loadSpecials();
    } catch (err) { console.error('Failed to save vacations', err); message.error('Failed to save vacations'); }
  };

  const deleteSpecial = async (sd: SpecialDay) => {
    if(!selectedUser || !sd.id) return;
    try {
      await calendarService.deleteSpecial(selectedUser, sd.id);
      message.success('Deleted');
      loadSpecials();
    } catch (err) { console.error('Failed to delete special day', err); message.error('Failed to delete'); }
  };

  const patternColumns = [
    { title:'Day', dataIndex:'weekday', key:'weekday', render:(v:number)=> weekdayLabels[(v+6)%7] },
    { title:'Active', dataIndex:'is_active', key:'is_active', render: (_:unknown, r:WorkingDayPattern)=> <Switch checked={r.is_active} onChange={val=> updatePatternField(r.weekday,'is_active', val)} /> },
    { title:'Hours', dataIndex:'hours', key:'hours', render: (_:unknown, r:WorkingDayPattern)=> <InputNumber min={0} max={24} value={r.hours} disabled={!r.is_active} onChange={val=> updatePatternField(r.weekday,'hours', val as number)} /> }
  ];

  const specialColumns = [
    { title:'Date', dataIndex:'date', key:'date' },
    { title:'Type', key:'type', render:(_:unknown, r:SpecialDay)=> r.is_working? <Tag color='green'>Working override</Tag>: <Tag color='volcano'>Non‑working</Tag> },
    { title:'Hours', dataIndex:'hours', key:'hours', render:(v:number|undefined|null)=> v ?? '-' },
    { title:'Reason', dataIndex:'reason', key:'reason', render:(v:string|undefined|null)=> v || '-' },
    { title:'Actions', key:'actions', render:(_:unknown, r:SpecialDay)=> r.id ? <AntButton size='small' danger onClick={()=> deleteSpecial(r)}>Delete</AntButton>: null }
  ];

  const userVacations = specialDays.filter(d=> !d.is_working && (((d.reason||'').toLowerCase().includes('vac')) || ((d.reason||'').toLowerCase().includes('vaca'))));

  return (
    <ManagementPageLayout
      kpis={kpiData()}
      kpiClassName='grid grid-cols-2 md:grid-cols-4 xl:grid-cols-6 gap-4 mb-4'
    >
      <div className='elegant-card p-4 flex flex-col h-full'>
        <div className='flex flex-wrap gap-2 items-end mb-4'>
          {authUser?.role === 'Tecnico' ? (
            <Tag icon={<UserOutlined />} color='blue'>
              {users[0]?.name || 'Me'}
            </Tag>
          ) : (
            <Select
              placeholder='User'
              style={{minWidth:200}}
              value={selectedUser ?? undefined}
              onChange={val=> setSelectedUser(val)}
              options={users.map(u=> ({ value:u.id, label:u.name }))}
            />
          )}
          <AppButton variant='ghost' size='sm' icon={<LeftOutlined />} onClick={prevWeek} title='Previous week' />
          <AppButton variant='primary' size='sm' onClick={thisWeek}>Today</AppButton>
          <AppButton variant='ghost' size='sm' icon={<RightOutlined />} onClick={nextWeek} title='Next week' />
          <AppButton variant='ghost' size='sm' icon={<ReloadOutlined />} title='Reload' onClick={()=> { loadPattern(); loadSpecials(); }} />
        </div>
        <Tabs
          defaultActiveKey='pattern'
          className='calendar-tabs flex-1 flex flex-col'
          items={[
            {
              key:'pattern',
              label:'Weekly pattern',
              children: (
                <div className='flex flex-col gap-3'>
                  <div className='text-xs mb-1 text-muted-foreground'>Week {weekStart.format('DD/MM')} - {weekEnd.format('DD/MM')}</div>
                  <Table size='small' pagination={false} dataSource={pattern} columns={patternColumns} rowKey='weekday' loading={loadingPattern} />
                  <div className='flex justify-end'>
                    <AppButton variant='primary' size='sm' onClick={savePattern} disabled={!selectedUser || authUser?.role === 'Tecnico'}>
                      Save pattern
                    </AppButton>
                  </div>
                </div>
              )
            },
            {
              key:'special',
              label:'Special days',
              children: (
                <div className='flex flex-col gap-3 h-full'>
                  <div className='flex gap-2 flex-wrap'>
                    <AppButton variant='secondary' size='sm' icon={<PlusOutlined />} onClick={openSpecialModal} disabled={!selectedUser}>New</AppButton>
                  </div>
                  <DatePicker.RangePicker value={[rangeStart, rangeEnd]} onChange={vals=> { if(vals){ setRangeStart(vals[0]!); setRangeEnd(vals[1]!); } }} style={{maxWidth:320}} />
                  <Table size='small' pagination={false} dataSource={specialDays.filter(d=> !(d.reason||'').toLowerCase().includes('vaca'))} columns={specialColumns} rowKey={(r)=> r.id? r.id: r.date+ r.reason} locale={{emptyText:'No special days'}} />
                </div>
              )
            },
            {
              key:'vac',
              label:'Vacations',
              children: (
                <div className='flex flex-col gap-3 h-full'>
                  <div className='flex gap-2 flex-wrap'>
                    <AppButton variant='primary' size='sm' onClick={openVacationModal} disabled={!selectedUser}>Add range</AppButton>
                  </div>
                  <DatePicker.RangePicker value={[rangeStart, rangeEnd]} onChange={vals=> { if(vals){ setRangeStart(vals[0]!); setRangeEnd(vals[1]!); } }} style={{maxWidth:320}} />
                  <Table size='small' pagination={false} dataSource={userVacations} columns={[{ title:'Date', dataIndex:'date'},{ title:'Reason', dataIndex:'reason'}]} rowKey={(r)=> r.id || r.date + (r.reason||'')} locale={{emptyText:'No vacations'}} />
                </div>
              )
            }
          ]}
        />
      </div>

  <ModalDialog open={specialModalOpen} title='New Special Day' onClose={()=> setSpecialModalOpen(false)} primary={{ label: 'Save', onClick: submitSpecial }}>
        <Form form={specialForm} layout='vertical'>
          <Form.Item name='date' label='Date' rules={[{ required: true, type: 'object', message: 'Please select a date' }]}> <DatePicker style={{width:'100%'}} /> </Form.Item>
          <Form.Item name='is_working' label='Working day' valuePropName='checked'> <Switch /> </Form.Item>
          <Form.Item name='hours' label='Hours (if working)'> <InputNumber min={0} max={24} style={{width:'100%'}} /> </Form.Item>
          <Form.Item name='reason' label='Reason'> <Input /> </Form.Item>
        </Form>
      </ModalDialog>

      <ModalDialog open={vacationModalOpen} title='User Vacation Range' onClose={()=> setVacationModalOpen(false)} primary={{ label: 'Save', onClick: submitVacationRange }}>
        <Form form={vacForm} layout='vertical'>
          <Form.Item name='range' label='Range' rules={[{ required: true, type: 'array', message: 'Please select a date range' }]}> <DatePicker.RangePicker style={{width:'100%'}} /> </Form.Item>
          <Form.Item name='reason' label='Reason'> <Input /> </Form.Item>
        </Form>
      </ModalDialog>
    </ManagementPageLayout>
  );
}
