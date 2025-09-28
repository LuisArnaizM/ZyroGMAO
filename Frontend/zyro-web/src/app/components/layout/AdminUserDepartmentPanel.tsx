"use client";

import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { Form, Input, Select, Tag, message, Switch } from 'antd';
import ModalDialog from '../ui/ModalDialog';
import type { ColumnsType } from 'antd/es/table';
import { EntityList } from '../data/EntityList';
import { UserService } from '../../services/user.service';
import { DepartmentService } from '../../services/department.service';
import { Department, Role, UserRead, UserUpdate, UserCreate } from '../../types';

const { Option } = Select;

const ROLE_OPTIONS = [
  { value: 'Admin', label: 'Admin' },
  { value: 'Supervisor', label: 'Supervisor' },
  { value: 'Tecnico', label: 'Técnico' },
  { value: 'Consultor', label: 'Consultor' },
];

type FormValues = {
  username?: string;
  first_name?: string;
  last_name?: string;
  email?: string;
  password?: string; // solo en create
  role: Role;
  department_id?: number | null;
  is_active?: boolean;
};

export default function AdminUserDepartmentPanel() {
  const userService = useMemo(() => new UserService(), []);
  const departmentService = useMemo(() => new DepartmentService(), []);

  const [users, setUsers] = useState<UserRead[]>([]);
  const [departments, setDepartments] = useState<Department[]>([]);
  const [loading, setLoading] = useState(false);
  const [modalOpen, setModalOpen] = useState(false);
  const [editing, setEditing] = useState<UserRead | null>(null);
  const [isCreate, setIsCreate] = useState(false);
  const [form] = Form.useForm<FormValues>();

  const depName = (id?: number | null) => departments.find(d => d.id === id)?.name || '-';

  const load = useCallback(async () => {
    try {
      setLoading(true);
      const [u, d] = await Promise.all([
        userService.getAll(),
        departmentService.getAll(),
      ]);
      setUsers(Array.isArray(u) ? u : []);
      setDepartments(Array.isArray(d) ? d : []);
    } catch (e) {
      console.error(e);
      message.error('Error cargando usuarios/departamentos');
    } finally {
      setLoading(false);
    }
  }, [userService, departmentService]);

  useEffect(() => { load(); }, [load]);

  const onOpenCreate = () => {
    setIsCreate(true);
    setEditing(null);
    form.resetFields();
    form.setFieldsValue({ is_active: true });
    setModalOpen(true);
  };

  const onOpenEdit = (u: UserRead) => {
    setIsCreate(false);
    setEditing(u);
    form.setFieldsValue({
      username: u.username,
      first_name: u.first_name,
      last_name: u.last_name,
      email: u.email,
      role: u.role,
      department_id: u.department_id ?? null,
      is_active: Boolean(u.is_active),
    });
    setModalOpen(true);
  };

  const onDelete = async (u: UserRead) => {
    try {
      setLoading(true);
      await userService.delete(u.id);
      message.success('Usuario eliminado');
      load();
    } catch (e) {
      console.error(e);
      message.error('Error eliminando usuario');
    } finally {
      setLoading(false);
    }
  };

  const onSubmit = async (values: FormValues) => {
    try {
      setLoading(true);
      if (isCreate) {
        const payload: UserCreate = {
          username: values.username!,
          first_name: values.first_name!,
          last_name: values.last_name!,
          email: values.email!,
          password: values.password!,
          role: values.role,
          department_id: values.department_id ?? undefined,
        };
        await userService.create(payload);
        message.success('Usuario creado');
      } else if (editing) {
        const payload: UserUpdate = {
          username: values.username,
          first_name: values.first_name,
          last_name: values.last_name,
          email: values.email,
          role: values.role,
          department_id: values.department_id ?? undefined,
          is_active: values.is_active !== undefined ? (values.is_active ? 1 : 0) : undefined,
        };
        await userService.update(editing.id, payload);
        message.success('Usuario actualizado');
      }
      setModalOpen(false);
      setEditing(null);
      form.resetFields();
      load();
    } catch (e) {
      console.error(e);
      message.error('Error guardando usuario');
    } finally {
      setLoading(false);
    }
  };

  const columns: ColumnsType<UserRead> = [
    { title: 'ID', dataIndex: 'id', key: 'id', width: 70 },
    { title: 'Usuario', dataIndex: 'username', key: 'username' },
    { title: 'Nombre', key: 'name', render: (_, r) => `${r.first_name} ${r.last_name}` },
    { title: 'Email', dataIndex: 'email', key: 'email' },
    { title: 'Rol', dataIndex: 'role', key: 'role', render: (role: string) => <Tag color="blue">{role}</Tag> },
    { title: 'Departamento', key: 'department', render: (_, r) => depName(r.department_id) },
    { title: 'Estado', key: 'is_active', render: (_, r) => <Tag color={r.is_active ? 'green' : 'red'}>{r.is_active ? 'Activo' : 'Inactivo'}</Tag> },
  ];

  return (
    <>
      <EntityList<UserRead>
        title="Usuarios"
        data={users}
        columns={columns}
        rowKey={(r) => r.id}
        loading={loading}
        createLabel="Nuevo Usuario"
        onCreate={onOpenCreate}
        onEdit={onOpenEdit}
        onDelete={(r) => onDelete(r as UserRead)}
        viewButtonLabel="Detalles"
        scrollX={900}
        scrollY={'calc(100vh - 300px)'}
      />

      <ModalDialog
        title={isCreate ? 'Crear Usuario' : editing ? `Editar: ${editing.first_name} ${editing.last_name}` : 'Editar Usuario'}
        open={modalOpen}
        onClose={() => { setModalOpen(false); setEditing(null); }}
        primary={{ label: isCreate ? 'Crear' : 'Guardar', onClick: () => form.submit(), loading }}
        secondary={{ label: 'Cancelar', onClick: () => { setModalOpen(false); setEditing(null); } }}
      >
        <Form<FormValues> form={form} layout="vertical" onFinish={onSubmit}>
          <Form.Item name="username" label="Usuario" rules={isCreate ? [{ required: true, message: 'Usuario requerido' }] : []}>
            <Input placeholder="usuario" />
          </Form.Item>
          <Form.Item name="first_name" label="Nombre" rules={isCreate ? [{ required: true, message: 'Nombre requerido' }] : []}>
            <Input />
          </Form.Item>
          <Form.Item name="last_name" label="Apellidos" rules={isCreate ? [{ required: true, message: 'Apellidos requeridos' }] : []}>
            <Input />
          </Form.Item>
          <Form.Item name="email" label="Email" rules={isCreate ? [{ required: true, message: 'Email requerido' }] : []}>
            <Input type="email" />
          </Form.Item>
          {isCreate && (
            <Form.Item name="password" label="Contraseña" rules={[{ required: true, message: 'Contraseña requerida' }]}> 
              <Input.Password />
            </Form.Item>
          )}
          <Form.Item name="role" label="Rol" rules={[{ required: true, message: 'Selecciona un rol' }]}>
            <Select placeholder="Selecciona rol">
              {ROLE_OPTIONS.map(opt => <Option key={opt.value} value={opt.value}>{opt.label}</Option>)}
            </Select>
          </Form.Item>
          <Form.Item name="department_id" label="Departamento">
            <Select allowClear placeholder="Selecciona departamento">
              {departments.map(d => <Option key={d.id} value={d.id}>{d.name}</Option>)}
            </Select>
          </Form.Item>
          {!isCreate && (
            <Form.Item name="is_active" label="Activo" valuePropName="checked">
              <Switch />
            </Form.Item>
          )}
        </Form>
      </ModalDialog>
    </>
  );
}
