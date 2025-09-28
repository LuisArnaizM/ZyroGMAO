import { configureStore } from '@reduxjs/toolkit';
import { persistStore, persistReducer } from 'redux-persist';
import storage from 'redux-persist/lib/storage';
import { combineReducers } from '@reduxjs/toolkit';

// Importar slices
import filtersSlice from './slices/filterSlice';
import dashboardSlice from './slices/dashboardSlice';
import kpiSlice from './slices/kpiSlice';

const rootReducer = combineReducers({
  filters: filtersSlice,
  dashboard: dashboardSlice, // ✅ Ahora dashboard existe
  kpi: kpiSlice,
});

const persistConfig = {
  key: 'root',
  storage,
  whitelist: ['filters'], // Solo persistir filtros
  blacklist: ['dashboard', 'kpi'], // KPI/Dashboard no se persisten (datos en tiempo real)
};

const persistedReducer = persistReducer(persistConfig, rootReducer);

export const store = configureStore({
  reducer: persistedReducer,
  middleware: (getDefaultMiddleware) =>
    getDefaultMiddleware({
      serializableCheck: {
        ignoredActions: ['persist/PERSIST', 'persist/REHYDRATE'],
      },
    }),
  devTools: process.env.NODE_ENV !== 'production',
});

export const persistor = persistStore(store);

export type RootState = ReturnType<typeof store.getState>;
export type AppDispatch = typeof store.dispatch;