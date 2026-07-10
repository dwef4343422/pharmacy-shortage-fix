import { create } from 'zustand';

export interface Medicine {
  id: string;
  name: string;
  name_arabic: string | null;
  current_stock: number;
  minimum_stock: number;
  required_quantity: number;
  priority: 'critical' | 'high' | 'medium' | 'safe';
  notes: string | null;
  ocr_confidence: number | null;
  is_duplicate_merged: boolean;
  merge_count: number;
}

export interface Report {
  id: string;
  title: string;
  created_at: string;
  updated_at: string;
  source_type: string;
  status: string;
  total_medicines: number;
  below_minimum_count: number;
  critical_count: number;
  total_required: number;
  default_min_stock: number;
  notes: string | null;
  medicines: Medicine[];
}

interface ReportState {
  currentReport: Report | null;
  isLoading: boolean;
  error: string | null;
  setReport: (report: Report | null) => void;
  setLoading: (isLoading: boolean) => void;
  setError: (error: string | null) => void;
  updateMedicineLocally: (id: string, updates: Partial<Medicine>) => void;
}

export const useReportStore = create<ReportState>((set) => ({
  currentReport: null,
  isLoading: false,
  error: null,
  setReport: (report) => set({ currentReport: report, error: null }),
  setLoading: (isLoading) => set({ isLoading }),
  setError: (error) => set({ error, isLoading: false }),
  updateMedicineLocally: (id, updates) =>
    set((state) => {
      if (!state.currentReport) return state;

      const updatedMedicines = state.currentReport.medicines.map((med) =>
        med.id === id ? { ...med, ...updates } : med
      );

      // We'll recalculate stats on the server, but could do a basic update here
      return {
        currentReport: {
          ...state.currentReport,
          medicines: updatedMedicines,
        },
      };
    }),
}));
