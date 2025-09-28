"use client";

import { useState, useEffect, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import { authService } from '@/services/auth.service';
import { apiClient } from '@/utils/api-client';
import { AuthUser } from '@/types';

export function useAuth() {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const router = useRouter();


  // Verificar autenticación al cargar
  useEffect(() => {
    const checkAuth = async () => {
      try {
        setLoading(true);
        console.log('useAuth - Starting auth check...');
        
        // ✅ Verificar que estamos en el cliente
        if (typeof window === 'undefined') {
          console.log('useAuth - Server side, skipping localStorage check');
          setLoading(false);
          return;
        }
        
        // Verificar si hay tokens guardados
        const accessToken = localStorage.getItem('access_token');
        const refreshToken = localStorage.getItem('refresh_token');
        const tokenExpiresAt = localStorage.getItem('token_expires_at');
        const userData = localStorage.getItem('user_data');
        
        console.log('useAuth - Found stored data:', { 
          hasAccessToken: !!accessToken, 
          hasRefreshToken: !!refreshToken,
          hasUserData: !!userData,
          tokenExpiresAt: tokenExpiresAt
        });
        
        if (accessToken) {
          try {
            console.log('useAuth - Restoring tokens in apiClient...');
            apiClient.setTokens(accessToken, refreshToken || undefined);
            console.log('useAuth - Tokens restored successfully');
          } catch (restoreError) {
            console.error('useAuth - Error restoring tokens:', restoreError);
          }
          
          // ✅ Verificar expiración solo si existe tokenExpiresAt
          if (tokenExpiresAt && tokenExpiresAt !== 'null') {
            const expirationTime = parseInt(tokenExpiresAt);
            
            console.log('useAuth - Token expiration check:', {
              expirationTime,
              currentTime: Date.now(),
              difference: expirationTime - Date.now(),
              isExpired: expirationTime <= Date.now(),
              hoursLeft: (expirationTime - Date.now()) / (1000 * 60 * 60)
            });

          } else {
            console.log('useAuth - No expiration time found, assuming token is valid');
          }
          
          try {
            // Verificar que el token sigue siendo válido obteniendo el perfil
            console.log('useAuth - Validating token with getMe...');
            const userProfile = await authService.getMe();
            console.log('useAuth - Token valid, setting user and authenticated:', userProfile);
            
            setUser(userProfile);
            setIsAuthenticated(true);
            localStorage.setItem('user_data', JSON.stringify(userProfile));
          } catch (err) {
            console.log('useAuth - Token invalid, clearing all data:', err);
            // Token inválido, limpiar datos
            localStorage.removeItem('access_token');
            localStorage.removeItem('refresh_token');
            localStorage.removeItem('token_expires_at');
            localStorage.removeItem('user_data');
            apiClient.clearTokens();
            setUser(null);
            setIsAuthenticated(false);
          }
        } else {
          console.log('useAuth - No access token found');
          setUser(null);
          setIsAuthenticated(false);
        }
      } catch (err) {
        console.error('useAuth - Error checking auth:', err);
        setUser(null);
        setIsAuthenticated(false);
      } finally {
        setLoading(false);
        console.log('useAuth - Auth check completed');
      }
    };

    checkAuth();
  }, []);

  // Login
  const login = useCallback(async (credentials: { username: string; password: string }): Promise<AuthUser> => {
    try {
      setLoading(true);
      setError(null);
      console.log('useAuth - Login started');
      
      // Primero hacer login para obtener tokens
      const tokenResponse = await authService.login({
        username: credentials.username,
        password: credentials.password,
      });
      
      console.log('useAuth - Token response received:', {
        hasAccessToken: !!tokenResponse.access_token,
        hasRefreshToken: !!tokenResponse.refresh_token,
        expiresIn: tokenResponse.expires_in
      });
      
      // Guardar tokens en localStorage
      localStorage.setItem('access_token', tokenResponse.access_token);
      if (tokenResponse.refresh_token) {
        localStorage.setItem('refresh_token', tokenResponse.refresh_token);
      }
      
      // ✅ CORRECCIÓN: Manejar expires_in como fecha ISO string
      let expirationTime = null;
      if (tokenResponse.expires_in) {
        try {
          // ✅ Convertir la fecha ISO string a timestamp
          expirationTime = new Date(tokenResponse.expires_in).getTime();
          localStorage.setItem('token_expires_at', String(expirationTime));
          
          console.log('useAuth - Saving token expiration:', {
            expires_in_iso: tokenResponse.expires_in,
            currentTime: Date.now(),
            expirationTime: expirationTime,
            expirationDate: new Date(expirationTime).toISOString(),
            isValid: !isNaN(expirationTime)
          });
        } catch (dateError) {
          console.error('useAuth - Error parsing expiration date:', dateError);
          expirationTime = null;
        }
      }

      // ✅ Configurar tokens en el ApiClient (sin la expiración por ahora)
      try {
        console.log('useAuth - Setting tokens in apiClient...');
        apiClient.setTokens(
          tokenResponse.access_token, 
          tokenResponse.refresh_token
          // ✅ No pasar expirationTime para evitar errores
        );
        console.log('useAuth - Tokens set successfully in apiClient');
      } catch (apiError) {
        console.error('useAuth - Error setting tokens in apiClient:', apiError);
      }

      // Luego obtener información del usuario
      console.log('useAuth - Getting user profile...');
      const userProfile = await authService.getMe();
      localStorage.setItem('user_data', JSON.stringify(userProfile));
      
      console.log('useAuth - Setting user and authenticated state:', userProfile);
      setUser(userProfile);
      setIsAuthenticated(true);
      
      console.log('useAuth - Login completed successfully');
      return userProfile;
    } catch (err: unknown) {
      const errorMessage = err instanceof Error ? err.message : 'Error al iniciar sesión';
      console.error('useAuth - Login error:', errorMessage);
      setError(errorMessage);
      setIsAuthenticated(false);
      throw new Error(errorMessage);
    } finally {
      setLoading(false);
    }
  }, []);

  // Logout
  const logout = useCallback(async () => {
    try {
      console.log('useAuth - Starting logout...');
      await authService.logout();
    } catch (error) {
      console.error('useAuth - Error during logout:', error);
    } finally {
      // Limpiar datos locales
      console.log('useAuth - Clearing all local data...');
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
      localStorage.removeItem('token_expires_at');
      localStorage.removeItem('user_data');
      localStorage.removeItem('redirect_after_login');
      apiClient.clearTokens();
      setUser(null);
      setIsAuthenticated(false);
      
      // Redirigir al login
      router.push('/login');
    }
  }, [router]);

  // ✅ Función para verificar roles
  const hasRole = useCallback((roles: string[]): boolean => {
    if (!user || !user.role) return false;
    return roles.includes(user.role);
  }, [user]);

  // ✅ Función para requerir autenticación
  const requireAuth = useCallback((): boolean => {
    if (!isAuthenticated) {
      router.push('/login');
      return false;
    }
    return true;
  }, [isAuthenticated, router]);

  return {
    user,
    loading,
    error,
    isAuthenticated,
    login,
    logout,
    hasRole,      
    requireAuth   
  };
}