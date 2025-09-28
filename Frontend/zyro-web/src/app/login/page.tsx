"use client";

import { useState, useEffect } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import {
  Card,
  Typography,
  Input,
  Button,
  Alert,
  Space,
  Divider,
  Spin
} from "antd";
import { UserOutlined, LockOutlined, LoginOutlined, EyeTwoTone, EyeInvisibleOutlined } from "@ant-design/icons";
import { useAuth } from "@/hooks/useAuth";

const { Title, Text } = Typography;

export default function LoginPage() {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  
  const { login, error, isAuthenticated, loading } = useAuth();
  const router = useRouter();
  const searchParams = useSearchParams();

  useEffect(() => {
    // Si ya está autenticado, redirigir inmediatamente
    if (!loading && isAuthenticated) {
      console.log('LoginPage - User already authenticated, redirecting...');
      // Priorizar redirect en query (?redirect=/ruta)
      const redirectParam = searchParams.get('redirect');
      const redirectUrl = redirectParam || localStorage.getItem('redirect_after_login');
      if (redirectUrl && redirectUrl !== '/login') {
        localStorage.removeItem('redirect_after_login');
        // Forzar recarga completa para hidratar estado protegido correctamente
        window.location.href = redirectUrl;
      } else {
        window.location.href = '/dashboard';
      }
    }
  }, [loading, isAuthenticated, router, searchParams]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!username.trim() || !password.trim()) {
      return;
    }

    setIsLoading(true);
    
    try {
      console.log('LoginPage - Attempting login...');
      
  const user = await login({
        username: username.trim(),
        password: password,
      });
      
  console.log('LoginPage - Login successful, hook will handle redirect', user?.username);

    } catch (err) {
      console.error("Error de login:", err);
    } finally {
      setIsLoading(false);
    }
  };


  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-blue-100 flex items-center justify-center p-6">
        <div className="text-center">
          <Spin size="large" />
          <div className="mt-4">
            <Text type="secondary">Verificando sesión existente...</Text>
          </div>
        </div>
      </div>
    );
  }
  
  if (isAuthenticated) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-blue-100 flex items-center justify-center p-6">
        <div className="text-center">
          <Spin size="large" />
          <div className="mt-4">
            <Text type="secondary">Ya tienes sesión activa, redirigiendo...</Text>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-blue-100 flex items-center justify-center p-6">
      <Card className="w-full max-w-md shadow-xl">
        <div className="p-8">
          <Space direction="vertical" size="large" className="w-full">
            {/* Header */}
            <div className="text-center">
              <div className="w-16 h-16 bg-blue-500 rounded-full flex items-center justify-center mx-auto mb-4">
                <UserOutlined className="text-white text-2xl" />
              </div>
              <Title level={2} className="!mb-2">
                Iniciar Sesión
              </Title>
              <Text type="secondary">
                Accede a tu cuenta de Zyro
              </Text>
            </div>

            <Divider />

            {/* Error Alert */}
            {error && (
              <Alert
                message="Error de autenticación"
                description={error}
                type="error"
                showIcon
              />
            )}

            {/* Login Form */}
            <form onSubmit={handleSubmit}>
              <Space direction="vertical" size="middle" className="w-full">
                <div>
                  <Text strong className="block mb-1">
                    Usuario o Email
                  </Text>
                  <Input
                    type="text"
                    placeholder="Introduce tu usuario o email"
                    value={username}
                    onChange={(e) => setUsername(e.target.value)}
                    size="large"
                    prefix={<UserOutlined />}
                    required
                    disabled={isLoading}
                  />
                </div>

                <div>
                  <Text strong className="block mb-1">
                    Contraseña
                  </Text>
                  <Input.Password
                    placeholder="Introduce tu contraseña"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    size="large"
                    prefix={<LockOutlined />}
                    iconRender={(visible) => (visible ? <EyeTwoTone /> : <EyeInvisibleOutlined />)}
                    required
                    disabled={isLoading}
                  />
                </div>

                <Button
                  type="primary"
                  htmlType="submit"
                  size="large"
                  loading={isLoading}
                  disabled={!username.trim() || !password.trim() || isLoading}
                  icon={<LoginOutlined />}
                  block
                  className="mt-4"
                >
                  {isLoading ? "Iniciando sesión..." : "Iniciar Sesión"}
                </Button>
              </Space>
            </form>

            <Divider />

            {/* Footer */}
            <div className="text-center">
              <Text type="secondary" className="text-xs block mb-2">
                ¿Problemas para acceder? Contacta con el administrador del sistema
              </Text>
              <Space className="text-xs text-gray-400">
                <Text type="secondary">Zyro</Text>
                <Text type="secondary">•</Text>
                <Text type="secondary">v1.0.0</Text>
              </Space>
            </div>
          </Space>
        </div>
      </Card>
    </div>
  );
}