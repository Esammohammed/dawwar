import { create } from 'zustand';

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

export const useFilterStore = create((set) => ({
  ...initialFilters,
  setFilter: (key, value) => set((state) => ({ ...state, [key]: value })),
  resetFilters: () => set(initialFilters),
}));
