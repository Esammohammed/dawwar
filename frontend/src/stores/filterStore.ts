import { create } from 'zustand';

export interface FilterState {
  type: string;
  governorate: string;
  city: string;
  minPrice: string;
  maxPrice: string;
  bedrooms: string;
  finishing: string;
  hasInstallments: boolean;
  setFilter: (key: string, value: any) => void;
  resetFilters: () => void;
}

const initialFilters = {
  type: '',
  governorate: '',
  city: '',
  minPrice: '',
  maxPrice: '',
  bedrooms: '',
  finishing: '',
  hasInstallments: false,
};

export const useFilterStore = create<FilterState>((set) => ({
  ...initialFilters,
  setFilter: (key, value) => set((state) => ({ ...state, [key]: value })),
  resetFilters: () => set(initialFilters),
}));
