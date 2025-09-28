'use client';
import { Provider, useDispatch } from 'react-redux';
import { PersistGate } from 'redux-persist/integration/react';
import { store, persistor } from '../store';
import type { AppDispatch } from '../store';
import { useEffect, useRef } from 'react';
import { fetchAssetsKpi, fetchFailuresKpi, fetchWorkordersKpi } from '../store/slices/kpiSlice';

interface ReduxProviderProps {
  children: React.ReactNode;
}

// Componente de carga mejorado
function LoadingComponent() {
  return (
    <div className="flex items-center justify-center min-h-screen bg-gray-50">
      <div className="text-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
        <p className="text-gray-600">Inicializando estado...</p>
      </div>
    </div>
  );
}

export function ReduxProvider({ children }: ReduxProviderProps) {
  // Small bootstrapper to load global KPIs once after rehydration
  const KpiBootstrapper = () => {
  const dispatch = useDispatch<AppDispatch>();
    const didRun = useRef(false);
    useEffect(() => {
      if (didRun.current) return;
      didRun.current = true;
      dispatch(fetchAssetsKpi());
      dispatch(fetchWorkordersKpi());
      dispatch(fetchFailuresKpi());
    }, [dispatch]);
    return null;
  };

  return (
    <Provider store={store}>
      <PersistGate 
        loading={<LoadingComponent />} 
        persistor={persistor}
        onBeforeLift={() => {
          console.log('🔄 Redux persist: Cargando estado guardado...');
        }}
      >
        <KpiBootstrapper />
        {children}
      </PersistGate>
    </Provider>
  );
}