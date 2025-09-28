"use client";

import { useEffect } from 'react';
import { Card, Typography, Spin, Button, Divider, Avatar, Descriptions, Tag } from 'antd';
import { UserOutlined, EditOutlined, LogoutOutlined } from '@ant-design/icons';
import { useAuth } from '@/hooks/useAuth';
import { useRouter } from 'next/navigation';

const { Title, Text } = Typography;

export default function ProfilePage() {
  const { user, loading, isAuthenticated, logout, requireAuth } = useAuth();
  const router = useRouter();

  // Verificar autenticación al cargar el componente
  useEffect(() => {
    if (!loading && !requireAuth()) {
      // requireAuth() ya redirige al login si no está autenticado
      return;
    }
  }, [loading, requireAuth]);

  // Mostrar loading mientras se verifica la autenticación
  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <Spin size="large" />
          <div className="mt-4">
            <Text>Verificando autenticación...</Text>
          </div>
        </div>
      </div>
    );
  }

  // Si no está autenticado, no mostrar nada (ya se redirigió al login)
  if (!isAuthenticated || !user) {
    return null;
  }

  const handleLogout = async () => {
    try {
      await logout();
    } catch (error) {
      console.error('Error during logout:', error);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 p-6 ">
      <div className="max-w-4xl mx-auto">
        <Card className="mb-6">
          <div className="text-center mb-6">
            <Avatar size={120} icon={<UserOutlined />} className="mb-4" />
            <Title level={2} className="!mb-2">
              {user.full_name || user.username}
            </Title>
            <Text type="secondary" className="text-lg">
              {user.email}
            </Text>
            <div className="mt-2">
              <Tag color="blue" className="text-sm px-3 py-1">
                {user.role}
              </Tag>
              <Tag color={user.is_active ? "green" : "red"} className="text-sm px-3 py-1">
                {user.is_active ? "Activo" : "Inactivo"}
              </Tag>
            </div>
          </div>

          <Divider />

          <Descriptions
            title="Información del Perfil"
            column={1}
            bordered
            size="middle"
          >
            <Descriptions.Item label="ID de Usuario">
              {user.id}
            </Descriptions.Item>
            <Descriptions.Item label="Nombre de Usuario">
              {user.username}
            </Descriptions.Item>
            <Descriptions.Item label="Email">
              {user.email}
            </Descriptions.Item>
            <Descriptions.Item label="Nombre Completo">
              {user.full_name || 'No especificado'}
            </Descriptions.Item>
            <Descriptions.Item label="Nombre">
              {user.first_name || 'No especificado'}
            </Descriptions.Item>
            <Descriptions.Item label="Apellidos">
              {user.last_name || 'No especificado'}
            </Descriptions.Item>
            <Descriptions.Item label="Rol">
              <Tag color="blue">{user.role}</Tag>
            </Descriptions.Item>
            <Descriptions.Item label="Estado">
              <Tag color={user.is_active ? "green" : "red"}>
                {user.is_active ? "Activo" : "Inactivo"}
              </Tag>
            </Descriptions.Item>
            {user.organization && (
              <>
                <Descriptions.Item label="Organización">
                  {user.organization.name}
                </Descriptions.Item>
                <Descriptions.Item label="Slug de Organización">
                  {user.organization.slug}
                </Descriptions.Item>
              </>
            )}
            {user.last_login && (
              <Descriptions.Item label="Último Acceso">
                {new Date(user.last_login).toLocaleString()}
              </Descriptions.Item>
            )}
            {user.created_at && (
              <Descriptions.Item label="Fecha de Registro">
                {new Date(user.created_at).toLocaleString()}
              </Descriptions.Item>
            )}
          </Descriptions>

          <div className="text-center mt-6">
            <Button 
              type="primary" 
              icon={<EditOutlined />} 
              size="large"
              className="mr-3"
              onClick={() => router.push('/profile/edit')}
            >
              Editar Perfil
            </Button>
            <Button 
              danger 
              icon={<LogoutOutlined />} 
              size="large"
              onClick={handleLogout}
            >
              Cerrar Sesión
            </Button>
          </div>
        </Card>
      </div>
    </div>
  );
}
