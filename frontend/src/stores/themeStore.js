import { create } from 'zustand';

const getInitialTheme = () => {
  const saved = localStorage.getItem('dawwar_theme');
  if (saved === 'light' || saved === 'dark') return saved;
  return 'light'; // Default to light mode (white mode)
};

export const useThemeStore = create((set) => ({
  theme: getInitialTheme(),
  toggleTheme: () =>
    set((state) => {
      const theme = state.theme === 'dark' ? 'light' : 'dark';
      localStorage.setItem('dawwar_theme', theme);
      document.documentElement.setAttribute('data-theme', theme);
      return { theme };
    }),
}));
