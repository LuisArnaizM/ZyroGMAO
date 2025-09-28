"use client";

import { useEffect, ReactNode } from 'react';
import { Spin, Typography, Alert } from 'antd';
import { useAuth } from '@/hooks/useAuth';
import { useRouter, usePathname } from 'next/navigation';

const { Text } = Typography;

interface ProtectedPageProps {
  children: ReactNode;
  requiredRoles?: string[];
  fallback?: ReactNode;
}

export default function ProtectedPage({ 
  children, 
  requiredRoles = [], 
  fallback
}: ProtectedPageProps) {
  const { user, loading, isAuthenticated } = useAuth();
  const router = useRouter();
  const pathname = usePathname();
  

  useEffect(() => {
    console.log('ProtectedPage - Debug info:', {
      loading,
      isAuthenticated,
      user: user ? { id: user.id, role: user.role, username: user.username } : null,
      pathname,
      requiredRoles
    });
  }, [loading, isAuthenticated, user, pathname, requiredRoles]);

  useEffect(() => {
    // ✅ Solo redirigir si NO está loading, NO está autenticado Y no hay usuario
    if (!loading && !isAuthenticated && !user) {
      console.log('ProtectedPage - Redirecting to login because not authenticated');
      
      // ✅ Solo guardar si no estamos ya en login y la ruta es válida
      if (pathname !== '/login' && pathname !== '/' && !pathname.startsWith('/login')) {
        console.log('ProtectedPage - Saving redirect URL:', pathname);
        localStorage.setItem('redirect_after_login', pathname);
      }
      
      // ✅ Pequeño delay para evitar conflictos de timing
      setTimeout(() => {
        router.push('/login');
      }, 100);
      return;
    }
  }, [loading, isAuthenticated, user, router, pathname]);

  // ✅ Mostrar loading mientras verifica autenticación
  if (loading) {
    console.log('ProtectedPage - Showing loading state');
    return fallback || (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center">
          <Spin size="large" />
          <div className="mt-4">
            <Text type="secondary">Verificando autenticación...</Text>
          </div>
        </div>
      </div>
    );
  }

  if (!isAuthenticated) {
    console.log('ProtectedPage - Not authenticated, showing redirect message');
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center">
          <Spin size="large" />
          <div className="mt-4">
            <Text type="secondary">Redirigiendo al login...</Text>
          </div>
        </div>
      </div>
    );
  }

  // ✅ Verificar que tenemos user después de confirmar autenticación
  if (!user) {
    console.log('ProtectedPage - Authenticated but no user data, loading...');
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center">
          <Spin size="large" />
          <div className="mt-4">
            <Text type="secondary">Cargando datos del usuario...</Text>
          </div>
        </div>
      </div>
    );
  }

  // ✅ Verificar roles si se especificaron
  if (requiredRoles.length > 0) {
    const userRole = user.role?.toLowerCase();
    const normalizedRequiredRoles = requiredRoles.map(role => role.toLowerCase());
    const hasRequiredRole = normalizedRequiredRoles.includes(userRole || '');

    console.log('ProtectedPage - Role check:', {
      userRole,
      requiredRoles,
      normalizedRequiredRoles,
      hasRequiredRole
    });

    if (!hasRequiredRole) {
      return (
        <div className="min-h-screen flex items-center justify-center bg-gray-50 p-6">
          <div className="max-w-md w-full">
            <Alert
              message="Acceso Denegado"
              description={
                <div className="text-center">
                  <Text>No tienes permisos para acceder a esta página.</Text>
                  <div className="mt-2">
                    <Text type="secondary">
                      Roles requeridos: {requiredRoles.join(', ')}
                    </Text>
                  </div>
                  <div className="mt-2">
                    <Text type="secondary">
                      Tu rol actual: {user.role}
                    </Text>
                  </div>
                </div>
              }
              type="warning"
              showIcon
              style={{ textAlign: 'center' }}
            />
          </div>
        </div>
      );
    }
  }

  console.log('ProtectedPage - All checks passed, rendering children');
  return <>{children}</>;
}