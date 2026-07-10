"use client";

import { useState } from "react";
import { ArrowUpDown, Edit2, Check, X } from "lucide-react";
import { Medicine, useReportStore } from "@/stores/reportStore";
import PriorityBadge from "./PriorityBadge";
import { api } from "@/lib/api";

interface ShortageTableProps {
  medicines: Medicine[];
  sortConfig: { key: keyof Medicine; direction: 'asc' | 'desc' };
  onSort: (key: keyof Medicine) => void;
  reportId: string;
}

export default function ShortageTable({ medicines, sortConfig, onSort, reportId }: ShortageTableProps) {
  const { updateMedicineLocally } = useReportStore();
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editValues, setEditValues] = useState<{ current_stock: number; minimum_stock: number; notes: string }>({
    current_stock: 0, minimum_stock: 10, notes: ""
  });

  const startEditing = (medicine: Medicine) => {
    setEditingId(medicine.id);
    setEditValues({
      current_stock: medicine.current_stock,
      minimum_stock: medicine.minimum_stock,
      notes: medicine.notes || "",
    });
  };

  const cancelEditing = () => {
    setEditingId(null);
  };

  const saveEditing = async (id: string) => {
    try {
      // Optimistic UI update
      updateMedicineLocally(id, {
        current_stock: editValues.current_stock,
        minimum_stock: editValues.minimum_stock,
        notes: editValues.notes,
        // UI won't immediately show new priority/required_qty unless we calculate it here too,
        // but the backend will return the correct ones anyway.
      });

      // Backend update
      const response = await api.put(`/reports/${reportId}/medicines/${id}`, {
        current_stock: editValues.current_stock,
        minimum_stock: editValues.minimum_stock,
        notes: editValues.notes,
      });

      // Clear editing state
      setEditingId(null);

      // Final update with server values (recalculated priority, etc)
      updateMedicineLocally(id, response.data);

    } catch (error) {
      // Restore editing state on error
      setEditingId(id);
      console.error("Failed to update medicine:", error);
      // Ideally show a toast error here
    }
  };

  const SortHeader = ({ label, sortKey }: { label: string, sortKey: keyof Medicine }) => {
    const isActive = sortConfig.key === sortKey;
    return (
      <th 
        className="px-4 py-3 text-left text-xs font-semibold text-slate-500 uppercase tracking-wider cursor-pointer hover:bg-slate-50 dark:hover:bg-slate-800 transition-colors"
        onClick={() => onSort(sortKey)}
      >
        <div className="flex items-center gap-1">
          {label}
          <ArrowUpDown className={`h-3 w-3 ${isActive ? 'text-medical-blue' : 'text-slate-300'}`} />
        </div>
      </th>
    );
  };

  if (medicines.length === 0) {
    return (
      <div className="p-12 text-center text-slate-500">
        No medicines match the current filters.
      </div>
    );
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm text-left">
        <thead className="bg-slate-50 dark:bg-slate-900 border-b border-slate-200 dark:border-slate-800">
          <tr>
            <th className="px-4 py-3 text-left text-xs font-semibold text-slate-500 uppercase tracking-wider w-10">#</th>
            <SortHeader label="Medicine Name" sortKey="name" />
            <SortHeader label="Stock" sortKey="current_stock" />
            <SortHeader label="Min" sortKey="minimum_stock" />
            <SortHeader label="Required" sortKey="required_quantity" />
            <SortHeader label="Priority" sortKey="priority" />
            <th className="px-4 py-3 text-left text-xs font-semibold text-slate-500 uppercase tracking-wider">Notes</th>
            <th className="px-4 py-3 text-right text-xs font-semibold text-slate-500 uppercase tracking-wider">Actions</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-200 dark:divide-slate-800 bg-white dark:bg-slate-950/50">
          {medicines.map((med, idx) => {
            const isEditing = editingId === med.id;
            
            return (
              <tr key={med.id} className="hover:bg-slate-50 dark:hover:bg-slate-900/50 transition-colors">
                <td className="px-4 py-3 text-slate-500">{idx + 1}</td>
                <td className="px-4 py-3 font-medium text-slate-900 dark:text-white">
                  <div>{med.name}</div>
                  {med.name_arabic && <div className="text-xs text-slate-500 mt-0.5">{med.name_arabic}</div>}
                  {med.is_duplicate_merged && (
                    <span className="inline-block mt-1 text-[10px] bg-blue-100 text-blue-700 px-1.5 py-0.5 rounded">
                      Merged ({med.merge_count})
                    </span>
                  )}
                </td>
                
                {/* Editable Cells */}
                {isEditing ? (
                  <>
                    <td className="px-4 py-3">
                      <input 
                        type="number" min="0" 
                        className="w-16 px-2 py-1 border rounded text-slate-900 dark:bg-slate-800 dark:text-white dark:border-slate-700 focus:ring-2 focus:ring-medical-blue outline-none"
                        value={editValues.current_stock}
                        onChange={(e) => setEditValues({...editValues, current_stock: parseInt(e.target.value) || 0})}
                      />
                    </td>
                    <td className="px-4 py-3">
                      <input 
                        type="number" min="0" 
                        className="w-16 px-2 py-1 border rounded text-slate-900 dark:bg-slate-800 dark:text-white dark:border-slate-700 focus:ring-2 focus:ring-medical-blue outline-none"
                        value={editValues.minimum_stock}
                        onChange={(e) => setEditValues({...editValues, minimum_stock: parseInt(e.target.value) || 0})}
                      />
                    </td>
                    <td className="px-4 py-3 font-semibold text-slate-400">
                      {Math.max(0, editValues.minimum_stock - editValues.current_stock)}
                    </td>
                    <td className="px-4 py-3 opacity-50"><PriorityBadge priority={med.priority} /></td>
                    <td className="px-4 py-3">
                      <input 
                        type="text"
                        className="w-full px-2 py-1 border rounded text-slate-900 dark:bg-slate-800 dark:text-white dark:border-slate-700 focus:ring-2 focus:ring-medical-blue outline-none"
                        value={editValues.notes}
                        onChange={(e) => setEditValues({...editValues, notes: e.target.value})}
                        placeholder="Add note..."
                      />
                    </td>
                    <td className="px-4 py-3 text-right">
                      <div className="flex justify-end gap-2">
                        <button onClick={() => saveEditing(med.id)} className="p-1.5 text-emerald-600 hover:bg-emerald-50 rounded-lg transition-colors">
                          <Check className="h-4 w-4" />
                        </button>
                        <button onClick={cancelEditing} className="p-1.5 text-red-600 hover:bg-red-50 rounded-lg transition-colors">
                          <X className="h-4 w-4" />
                        </button>
                      </div>
                    </td>
                  </>
                ) : (
                  <>
                    <td className="px-4 py-3">{med.current_stock}</td>
                    <td className="px-4 py-3 text-slate-500">{med.minimum_stock}</td>
                    <td className="px-4 py-3 font-semibold text-slate-900 dark:text-white">{med.required_quantity}</td>
                    <td className="px-4 py-3"><PriorityBadge priority={med.priority} /></td>
                    <td className="px-4 py-3 text-slate-500 max-w-[200px] truncate" title={med.notes || ""}>
                      {med.notes || "-"}
                    </td>
                    <td className="px-4 py-3 text-right">
                      <button 
                        onClick={() => startEditing(med)}
                        className="p-1.5 text-slate-400 hover:text-medical-blue hover:bg-blue-50 dark:hover:bg-blue-900/20 rounded-lg transition-colors"
                      >
                        <Edit2 className="h-4 w-4" />
                      </button>
                    </td>
                  </>
                )}
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
