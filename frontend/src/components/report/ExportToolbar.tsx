"use client";

import { useState } from "react";
import { Copy, Check, Download, FileSpreadsheet, FileText, Printer, Loader2 } from "lucide-react";
import { api } from "@/lib/api";
import { useReportStore } from "@/stores/reportStore";

interface ExportToolbarProps {
  reportId: string;
}

export default function ExportToolbar({ reportId }: ExportToolbarProps) {
  const [isExporting, setIsExporting] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);
  const { currentReport } = useReportStore();

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

  const buildReportText = (): string => {
    if (!currentReport) return "";
    const r = currentReport;
    const lines: string[] = [];
    lines.push(r.title);
    lines.push(`Generated: ${new Date(r.created_at).toLocaleString()}  |  Source: ${r.source_type}`);
    lines.push("");
    lines.push("SUMMARY");
    lines.push(`- Total Medicines: ${r.total_medicines}`);
    lines.push(`- Total Required: ${r.total_required}`);
    lines.push(`- Critical Items: ${r.critical_count}`);
    lines.push(`- Below Minimum: ${r.below_minimum_count}`);
    lines.push("");
    lines.push("MEDICINES");
    r.medicines.forEach((m, i) => {
      lines.push(
        `${i + 1}. ${m.name}${m.name_arabic ? ` (${m.name_arabic})` : ""} — ` +
        `Current: ${m.current_stock}, Min: ${m.minimum_stock}, ` +
        `Required: ${m.required_quantity}, Priority: ${m.priority}` +
        (m.notes ? `, Notes: ${m.notes}` : "")
      );
    });
    return lines.join("\n");
  };

  const handleCopy = async () => {
    const text = buildReportText();
    if (!text) return;
    try {
      if (navigator.clipboard && window.isSecureContext) {
        await navigator.clipboard.writeText(text);
      } else {
        // Fallback for non-secure contexts (http://localhost, etc.)
        const ta = document.createElement("textarea");
        ta.value = text;
        ta.style.position = "fixed";
        ta.style.opacity = "0";
        document.body.appendChild(ta);
        ta.select();
        document.execCommand("copy");
        document.body.removeChild(ta);
      }
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      console.error("Failed to copy report:", err);
      alert("Failed to copy report. Please try again.");
    }
  };

  return (
    <div className="flex flex-wrap items-center gap-2">
      <button
        onClick={handleCopy}
        disabled={!currentReport}
        className="flex items-center gap-1.5 px-4 py-2 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-xl text-sm font-medium text-slate-700 dark:text-slate-200 shadow-sm hover:bg-slate-50 dark:hover:bg-slate-800 transition-colors disabled:opacity-50"
      >
        {copied ? <Check className="h-4 w-4 text-emerald-600" /> : <Copy className="h-4 w-4" />}
        {copied ? "Copied!" : "Copy Report"}
      </button>

      <div className="flex items-center gap-2 bg-slate-100 dark:bg-slate-800 p-1 rounded-xl">
        <button
          onClick={() => handleExport('pdf')}
          disabled={!!isExporting}
          className="flex items-center gap-1.5 px-3 py-1.5 text-sm font-medium text-red-600 hover:bg-white dark:hover:bg-slate-700 rounded-lg transition-colors disabled:opacity-50"
        >
          {isExporting === 'pdf' ? <Loader2 className="h-4 w-4 animate-spin" /> : <FileText className="h-4 w-4" />}
          Download PDF
        </button>
        <button
          onClick={() => handleExport('excel')}
          disabled={!!isExporting}
          className="flex items-center gap-1.5 px-3 py-1.5 text-sm font-medium text-emerald-600 hover:bg-white dark:hover:bg-slate-700 rounded-lg transition-colors disabled:opacity-50"
        >
          {isExporting === 'excel' ? <Loader2 className="h-4 w-4 animate-spin" /> : <FileSpreadsheet className="h-4 w-4" />}
          Excel
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
