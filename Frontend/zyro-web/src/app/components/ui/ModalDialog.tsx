"use client";
import React from 'react';
import { Modal } from 'antd';
import { AppButton } from './AppButton';

type Action = {
  label?: string;
  onClick?: () => void;
  loading?: boolean;
  disabled?: boolean;
};

type Props = {
  open: boolean;
  title?: React.ReactNode;
  onClose: () => void;
  children?: React.ReactNode;
  width?: number;
  primary?: Action;
  secondary?: Action;
  centered?: boolean;
  footer?: React.ReactNode | null;
  className?: string;
};

export const ModalDialog: React.FC<Props> = ({ open, title, onClose, children, width = 960, primary, secondary, centered = true, footer, className }) => {
  const defaultFooter = footer === undefined ? (
    <div className="flex justify-end gap-2">
      {secondary ? (
        <AppButton variant="ghost" onClick={secondary.onClick || onClose} disabled={secondary.disabled}>
          {secondary.label || 'Cancel'}
        </AppButton>
      ) : (
        <AppButton variant="ghost" onClick={onClose}>Cancel</AppButton>
      )}
      {primary && (
        <AppButton variant="primary" onClick={primary.onClick} loading={primary.loading} disabled={primary.disabled}>
          {primary.label || 'Ok'}
        </AppButton>
      )}
    </div>
  ) : footer;

  return (
    <Modal
      title={title}
      open={open}
      onCancel={onClose}
      footer={null}
      width={width}
      centered={centered}
      className={`wide-modal ${className || ''}`}
      bodyStyle={{ maxHeight: '72vh', overflowY: 'auto', paddingTop: 12, paddingBottom: 12 }}
    >
      <div>
        {children}
        <div style={{ marginTop: 16 }}>
          {defaultFooter}
        </div>
      </div>
    </Modal>
  );
};

export default ModalDialog;
