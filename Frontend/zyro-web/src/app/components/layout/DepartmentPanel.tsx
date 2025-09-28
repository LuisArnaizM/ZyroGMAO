"use client";

import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { Form, Input, Select, Switch, message } from 'antd';
import ModalDialog from '../ui/ModalDialog';
import type { ColumnsType } from 'antd/es/table';
import { EntityList } from '../data/EntityList';
import { Department, DepartmentCreate, DepartmentUpdate, UserRead } from '@/types';
import { DepartmentService } from '@/services/department.service';
import { UserService } from '@/services/user.service';
import { useAuth } from '@/hooks/useAuth';
import { useRouter } from 'next/navigation';

type DepForm = {
  name?: string;
  description?: string;
  parent_id?: number | null;
  manager_id?: number | null;
  is_active?: boolean;
};

export default function DepartmentPanel() {
  const departmentService = useMemo(() => new DepartmentService(), []);
  const userService = useMemo(() => new UserService(), []);
  const { user } = useAuth();
  const { Option } = Select;
  const router = useRouter();

  const [deps, setDeps] = useState<Department[]>([]);
  const [techs, setTechs] = useState<UserRead[]>([]);
  const [loading, setLoading] = useState(false);
  const [modalOpen, setModalOpen] = useState(false);
  const [editing, setEditing] = useState<Department | null>(null);
  const [isCreate, setIsCreate] = useState(false);
  const [form] = Form.useForm<DepForm>();

  const load = useCallback(async () => {
    try {
      setLoading(true);
      const [d, u] = await Promise.all([
        departmentService.getAll(),
        userService.getByRole('Supervisor').then(a=>a).catch(()=>[]),
      ]);
      setDeps(Array.isArray(d) ? d : []);
      setTechs(Array.isArray(u) ? u : []);
    } catch (e) {
      console.error(e);
      message.error('Error cargando departamentos');
    } finally {
      setLoading(false);
    }
  }, [departmentService, userService]);

  useEffect(() => { load(); }, [load]);

  const onOpenCreate = () => {
    setIsCreate(true);
    setEditing(null);
    form.resetFields();
    form.setFieldsValue({ is_active: true });
    setModalOpen(true);
  };

  const onOpenEdit = (d: Department) => {
    setIsCreate(false);
    setEditing(d);
    form.setFieldsValue({
      name: d.name,
      description: d.description ?? undefined,
      parent_id: d.parent_id ?? null,
      manager_id: d.manager_id ?? null,
      is_active: d.is_active,
    });
    setModalOpen(true);
  };

  const onDelete = async (d: Department) => {
    try {
      setLoading(true);
      await departmentService.delete(d.id);
      message.success('Departamento eliminado');
      load();
    } catch (e) {
      console.error(e);
      message.error('Error eliminando departamento');
    } finally {
      setLoading(false);
    }
  };

  const onSubmit = async (values: DepForm) => {
    try {
      setLoading(true);
      if (isCreate) {
        const orgId = user?.organization_id;
        if (!orgId) {
          message.error('No se pudo determinar la organización del usuario');
          return;
        }
        const payload: DepartmentCreate = {
          name: values.name!,
          description: values.description,
          parent_id: values.parent_id ?? null,
          manager_id: values.manager_id ?? null,
          organization_id: orgId,
          is_active: values.is_active ?? true,
        };
        await departmentService.create(payload);
        message.success('Departamento creado');
      } else if (editing) {
        const payload: DepartmentUpdate = {
          name: values.name,
          description: values.description,
          parent_id: values.parent_id ?? null,
          manager_id: values.manager_id ?? null,
          is_active: values.is_active,
        };
        await departmentService.update(editing.id, payload);
        message.success('Departamento actualizado');
      }
      setModalOpen(false);
      setEditing(null);
      form.resetFields();
      load();
    } catch (e) {
      console.error(e);
      message.error('Error guardando departamento');
    } finally {
      setLoading(false);
    }
  };

  const columns: ColumnsType<Department> = [
    { title: 'ID', dataIndex: 'id', key: 'id', width: 70 },
    { title: 'Nombre', dataIndex: 'name', key: 'name' },
    { title: 'Descripción', dataIndex: 'description', key: 'description' },
    { title: 'Padre', dataIndex: 'parent_id', key: 'parent_id' },
    { title: 'Manager', dataIndex: 'manager_id', key: 'manager_id' },
    { title: 'Activo', dataIndex: 'is_active', key: 'is_active', render: (v: boolean) => v ? 'Sí' : 'No' },
  ];

  return (
    <>
      <EntityList<Department>
        title="Departamentos"
        data={deps}
        columns={columns}
        rowKey={(r) => r.id}
        loading={loading}
        createLabel="Nuevo Departamento"
        onCreate={onOpenCreate}
        onEdit={(r) => onOpenEdit(r as Department)}
        onDelete={(r) => onDelete(r as Department)}
        onView={(r) => router.push(`/admin/departments/${(r as Department).id}`)}
        viewButtonLabel="Organigrama"
        scrollX={900}
        scrollY={'calc(100vh - 300px)'}
      />

      <ModalDialog
        title={isCreate ? 'Crear Departamento' : editing ? `Editar: ${editing.name}` : 'Editar Departamento'}
        open={modalOpen}
        onClose={() => { setModalOpen(false); setEditing(null); }}
        primary={{ label: isCreate ? 'Crear' : 'Guardar', onClick: () => form.submit(), loading }}
        secondary={{ label: 'Cancelar', onClick: () => { setModalOpen(false); setEditing(null); } }}
      >
        <Form<DepForm> form={form} layout="vertical" onFinish={onSubmit}>
          <Form.Item name="name" label="Nombre" rules={[{ required: true, message: 'Nombre requerido' }]}> 
            <Input />
          </Form.Item>
          <Form.Item name="description" label="Descripción"> 
            <Input.TextArea rows={3} />
          </Form.Item>
          <Form.Item name="parent_id" label="Departamento Padre">
            <Select allowClear placeholder="Selecciona padre">
              {deps.map(d => <Option key={d.id} value={d.id}>{d.name}</Option>)}
            </Select>
          </Form.Item>
          <Form.Item name="manager_id" label="Responsable">
            <Select allowClear placeholder="Selecciona responsable">
              {techs.map(u => <Option key={u.id} value={u.id}>{u.first_name} {u.last_name}</Option>)}
            </Select>
          </Form.Item>
          <Form.Item name="is_active" label="Activo" valuePropName="checked">
            <Switch />
          </Form.Item>
        </Form>
      </ModalDialog>
  {/* Doble click sobre fila para ver organigrama */}
  {/* Nota: EntityList ya hace onDoubleClick -> onView(record). Usamos onView redirigiendo */}
    </>
  );
}
