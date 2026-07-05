import { create } from 'zustand';
import { persist } from 'zustand/middleware';

interface Settings {
  default_min_stock: number;
  language: 'en' | 'ar';
  theme: 'light' | 'dark' | 'system';
  export_format: 'excel' | 'pdf' | 'csv';
  ocr_sensitivity: 'low' | 'medium' | 'high';
}

interface SettingsState {
  settings: Settings;
  updateSettings: (newSettings: Partial<Settings>) => void;
}

export const useSettingsStore = create<SettingsState>()(
  persist(
    (set) => ({
      settings: {
        default_min_stock: 10,
        language: 'en',
        theme: 'light',
        export_format: 'excel',
        ocr_sensitivity: 'medium',
      },
      updateSettings: (newSettings) =>
        set((state) => ({
          settings: { ...state.settings, ...newSettings },
        })),
    }),
    {
      name: 'pharmacy-settings',
    }
  )
);
