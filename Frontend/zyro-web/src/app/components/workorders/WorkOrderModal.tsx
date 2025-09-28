"use client";
import React, { useEffect, useMemo } from 'react';
import { Form, Input, Select, DatePicker, message } from 'antd';
import ModalDialog from '../ui/ModalDialog';
import dayjs from 'dayjs';
import { WorkOrderService } from '../../services/workorder.service';
import { AssetRead, WorkOrderCreate } from '../../types';
import { apiClient } from '../../utils/api-client';

const { Option } = Select;

type Props = {
  open: boolean;
  onClose: () => void;
  onCreated?: () => void;
  prefill?: Partial<WorkOrderCreate> | undefined;
  assets?: AssetRead[];
};

export const WorkOrderModal: React.FC<Props> = ({ open, onClose, onCreated, prefill, assets = [] }) => {
  const [form] = Form.useForm();
  // Access apiClient via global if available, otherwise create without it (service will use default)
  const service = useMemo(() => new WorkOrderService(apiClient), []);

  useEffect(() => {
    if (open) {
      form.resetFields();
      if (prefill) {
        const values = { ...prefill };
        if (values.scheduled_date) {
          (values as Record<string, unknown>).scheduled_date = dayjs(values.scheduled_date);
        }
        // Asegurarse de que failure_id se setea si viene en prefill
        if (values.failure_id) {
          (values as Record<string, unknown>).failure_id = values.failure_id;
        }
        form.setFieldsValue(values);
      }
    }
  }, [open, prefill, form]);

  const handleSubmit = async (values: Record<string, unknown>) => {
    try {
      const payload: WorkOrderCreate = {
        title: String(values.title || ''),
        description: values.description ? String(values.description) : undefined,
        work_type: (values.work_type as string) || 'REPAIR',
        priority: (values.priority as string) || undefined,
        estimated_hours: values.estimated_hours as unknown as number | undefined,
        estimated_cost: values.estimated_cost as unknown as number | undefined,
        scheduled_date: values.scheduled_date ? dayjs(values.scheduled_date as dayjs.Dayjs).toISOString() : undefined,
        asset_id: values.asset_id as unknown as number,
        assigned_to: values.assigned_to as unknown as number | undefined,
        // Asegurarse de que failure_id se envía si está presente
        failure_id: values.failure_id !== undefined ? (values.failure_id as number) : undefined,
      };
      await service.createWorkOrder(payload);
      message.success('Work order created');
      if (onCreated) onCreated();
      onClose();
    } catch (e) {
      console.error('Create workorder error', e);
      message.error('Error creating work order');
    }
  };

  return (
    <ModalDialog
      open={open}
      title="Create Work Order"
      onClose={onClose}
      width={720}
      primary={{ label: 'Create', onClick: () => form.submit(), loading: false }}
      secondary={{ label: 'Cancel', onClick: onClose }}
    >
      <Form form={form} layout="vertical" onFinish={handleSubmit} initialValues={{ priority: 'MEDIUM', work_type: 'REPAIR' }}>
        {/* Campo oculto para failure_id si viene en prefill */}
        {prefill?.failure_id && (
          <Form.Item name="failure_id" initialValue={prefill.failure_id} style={{ display: 'none' }}>
            <Input type="hidden" />
          </Form.Item>
        )}
        <Form.Item name="title" label="Title" rules={[{ required: true, message: 'Please enter a title' }]}>
          <Input />
        </Form.Item>
        <Form.Item name="description" label="Description">
          <Input.TextArea rows={3} />
        </Form.Item>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <Form.Item name="asset_id" label="Asset" rules={[{ required: true, message: 'Select an asset' }]}>
            <Select placeholder="Select asset">
              {assets.map(a => <Option key={a.id} value={a.id}>{a.name}</Option>)}
            </Select>
          </Form.Item>
          <Form.Item name="priority" label="Priority">
            <Select>
              <Option value="LOW">Low</Option>
              <Option value="MEDIUM">Medium</Option>
              <Option value="HIGH">High</Option>
            </Select>
          </Form.Item>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <Form.Item name="work_type" label="Type">
            <Select>
              <Option value="REPAIR">Repair</Option>
              <Option value="INSPECTION">Inspection</Option>
              <Option value="MAINTENANCE">Maintenance</Option>
            </Select>
          </Form.Item>
          <Form.Item name="scheduled_date" label="Scheduled Date">
            <DatePicker showTime className="w-full" />
          </Form.Item>
        </div>

      </Form>
    </ModalDialog>
  );
};

export default WorkOrderModal;
