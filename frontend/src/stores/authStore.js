import { create } from 'zustand';

export const useAuthStore = create((set) => ({
  user: JSON.parse(localStorage.getItem('dawwar_user') || 'null'),
  accessToken: localStorage.getItem('dawwar_access_token'),
  refreshToken: localStorage.getItem('dawwar_refresh_token'),
  setAuth: (user, access, refresh) => {
    localStorage.setItem('dawwar_user', JSON.stringify(user));
    localStorage.setItem('dawwar_access_token', access);
    localStorage.setItem('dawwar_refresh_token', refresh);
    set({ user, accessToken: access, refreshToken: refresh });
  },
  logout: () => {
    localStorage.removeItem('dawwar_user');
    localStorage.removeItem('dawwar_access_token');
    localStorage.removeItem('dawwar_refresh_token');
    set({ user: null, accessToken: null, refreshToken: null });
  },
}));
