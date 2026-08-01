import axios from 'axios';
import { useAuthStore } from '../stores/authStore';

const api = axios.create({
  baseURL: '/api',
  headers: {
    'Content-Type': 'application/json',
  },
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('dawwar_access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Single-flight refresh: concurrent 401s share one refresh request.
let refreshPromise = null;

const refreshTokens = () => {
  if (!refreshPromise) {
    const refresh = localStorage.getItem('dawwar_refresh_token');
    refreshPromise = axios
      .post('/api/auth/token/refresh/', { refresh })
      .then((res) => {
        useAuthStore.getState().setTokens(res.data.access, res.data.refresh);
        return res.data.access;
      })
      .finally(() => {
        refreshPromise = null;
      });
  }
  return refreshPromise;
};

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const { config, response } = error;
    const isAuthCall = config?.url?.includes('/auth/');
    const hasRefresh = !!localStorage.getItem('dawwar_refresh_token');
    if (response?.status === 401 && !config._retry && !isAuthCall && hasRefresh) {
      config._retry = true;
      try {
        const access = await refreshTokens();
        config.headers.Authorization = `Bearer ${access}`;
        return api(config);
      } catch (refreshError) {
        useAuthStore.getState().logout();
        return Promise.reject(refreshError);
      }
    }
    return Promise.reject(error);
  }
);

export default api;
