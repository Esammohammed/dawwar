import { create } from 'zustand';

const initialFilters = {
  type: '',
  propertyType: '',
  governorate: '',
  city: '',
  minPrice: '',
  maxPrice: '',
  bedrooms: '',
  finishing: '',
  hasInstallments: false,
  is_verified_exit: false,
};

export const useFilterStore = create((set) => ({
  ...initialFilters,
  setFilter: (key, value) => set((state) => ({ ...state, [key]: value })),
  resetFilters: () => set(initialFilters),
}));
