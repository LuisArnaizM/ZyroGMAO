import { createSlice, PayloadAction } from '@reduxjs/toolkit';

interface FiltersState {
  assets: {
    search: string;
    location: string[];
    responsibleId: string[];
  };
}

const initialState: FiltersState = {
  assets: {
    search: '',
    location: [],
    responsibleId: [],
  },
};

// Función para contar filtros activos (tipada correctamente)
// eslint-disable-next-line @typescript-eslint/no-unused-vars
const countActiveFilters = (filters: Record<string, unknown>): number => {
  let count = 0;
  
  Object.entries(filters).forEach(([key, value]) => {
    if (key === 'search' && typeof value === 'string' && value.length > 0) {
      count++;
    }
    if (Array.isArray(value) && value.length > 0) {
      count++;
    }
  });
  
  return count;
};

const filtersSlice = createSlice({
  name: 'filters',
  initialState,
  reducers: {
    setAssetFilters: (state, action: PayloadAction<Partial<FiltersState['assets']>>) => {
      state.assets = { ...state.assets, ...action.payload };
    },
    
    clearAssetFilters: (state) => {
      state.assets = initialState.assets;
    },
  },
});

export const { setAssetFilters, clearAssetFilters } = filtersSlice.actions;
export default filtersSlice.reducer;