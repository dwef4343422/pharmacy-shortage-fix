"use client";

import { useState } from "react";
import { Download, FileSpreadsheet, FileText, Printer, Loader2 } from "lucide-react";
import { api } from "@/lib/api";

interface ExportToolbarProps {
  reportId: string;
}

export default function ExportToolbar({ reportId }: ExportToolbarProps) {
  const [isExporting, setIsExporting] = useState<string | null>(null);

  const handleExport = async (format: 'excel' | 'csv' | 'pdf') => {
    setIsExporting(format);
    try {
      const response = await api.get(`/reports/${reportId}/export?format=${format}`, {
        responseType: 'blob', // Important for file downloads
      });
      
      // Create a blob link to download
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      
      const extension = format === 'excel' ? 'xlsx' : format;
      link.setAttribute('download', `shortage_report_${reportId.substring(0,8)}.${extension}`);
      
      document.body.appendChild(link);
      link.click();
      
      // Clean up
      link.parentNode?.removeChild(link);
      window.URL.revokeObjectURL(url);
    } catch (error) {
      console.error(`Failed to export ${format}:`, error);
      alert(`Failed to export ${format.toUpperCase()}. Please try again.`);
    } finally {
      setIsExporting(null);
    }
  };

  const handlePrint = () => {
    window.print();
  };

  return (
    <div className="flex items-center gap-2">
      <div className="hidden sm:flex items-center gap-2 bg-slate-100 dark:bg-slate-800 p-1 rounded-xl">
        <button
          onClick={() => handleExport('excel')}
          disabled={!!isExporting}
          className="flex items-center gap-1.5 px-3 py-1.5 text-sm font-medium text-emerald-600 hover:bg-white dark:hover:bg-slate-700 rounded-lg transition-colors disabled:opacity-50"
        >
          {isExporting === 'excel' ? <Loader2 className="h-4 w-4 animate-spin" /> : <FileSpreadsheet className="h-4 w-4" />}
          Excel
        </button>
        <button
          onClick={() => handleExport('pdf')}
          disabled={!!isExporting}
          className="flex items-center gap-1.5 px-3 py-1.5 text-sm font-medium text-red-600 hover:bg-white dark:hover:bg-slate-700 rounded-lg transition-colors disabled:opacity-50"
        >
          {isExporting === 'pdf' ? <Loader2 className="h-4 w-4 animate-spin" /> : <FileText className="h-4 w-4" />}
          PDF
        </button>
        <button
          onClick={() => handleExport('csv')}
          disabled={!!isExporting}
          className="flex items-center gap-1.5 px-3 py-1.5 text-sm font-medium text-slate-600 dark:text-slate-300 hover:bg-white dark:hover:bg-slate-700 rounded-lg transition-colors disabled:opacity-50"
        >
          {isExporting === 'csv' ? <Loader2 className="h-4 w-4 animate-spin" /> : <Download className="h-4 w-4" />}
          CSV
        </button>
      </div>

      <button
        onClick={handlePrint}
        className="flex items-center gap-1.5 px-4 py-2 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-xl text-sm font-medium text-slate-700 dark:text-slate-200 shadow-sm hover:bg-slate-50 dark:hover:bg-slate-800 transition-colors"
      >
        <Printer className="h-4 w-4" />
        <span className="hidden sm:inline">Print</span>
      </button>
    </div>
  );
}
