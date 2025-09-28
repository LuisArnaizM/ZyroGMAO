"use client";

import React from 'react';
import { ConfigProvider } from 'antd';
import { AntdRegistry } from '@ant-design/nextjs-registry';

// Configuración del tema
const theme = {
  token: {
    colorPrimary: '#3b82f6', // Blue-500 similar a Chakra
    colorSuccess: '#10b981', // Green-500
    colorWarning: '#f59e0b', // Yellow-500
    colorError: '#ef4444', // Red-500
    borderRadius: 6,
    wireframe: false,
  },
  components: {
    Button: {
      colorPrimary: '#3b82f6',
      algorithm: true,
    },
    Input: {
      borderRadius: 6,
    },
    Card: {
      borderRadius: 8,
    },
  },
};

interface AntdProviderProps {
  children: React.ReactNode;
}

export function AntdProvider({ children }: AntdProviderProps) {
  return (
    <AntdRegistry>
      <ConfigProvider theme={theme}>
        {children}
      </ConfigProvider>
    </AntdRegistry>
  );
}
