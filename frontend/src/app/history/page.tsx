"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { api } from "@/lib/api";
import { FileText, History as HistoryIcon, Search, AlertCircle, Loader2 } from "lucide-react";
import PriorityBadge from "@/components/report/PriorityBadge";

interface ReportSummary {
  id: string;
  title: string;
  created_at: string;
  source_type: string;
  status: string;
  total_medicines: number;
  below_minimum_count: number;
  critical_count: number;
}

export default function HistoryPage() {
  const [reports, setReports] = useState<ReportSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState("");

  useEffect(() => {
    const fetchHistory = async () => {
      try {
        setLoading(true);
        const response = await api.get('/reports');
        setReports(response.data.reports || []);
      } catch (err: any) {
        console.error("Failed to load history:", err);
        setError("Could not load report history. Please try again later.");
      } finally {
        setLoading(false);
      }
    };

    fetchHistory();
  }, []);

  const filteredReports = reports.filter(r => 
    r.title.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <div className="space-y-6 animate-in fade-in duration-500">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-white flex items-center gap-2">
            <HistoryIcon className="h-6 w-6" />
            Report History
          </h1>
          <p className="text-slate-500 text-sm mt-1">
            View and re-download past shortage reports.
          </p>
        </div>
        <div className="relative">
          <div className="pointer-events-none absolute inset-y-0 left-0 flex items-center pl-3">
            <Search className="h-4 w-4 text-slate-400" />
          </div>
          <input
            type="text"
            className="block w-full sm:w-64 rounded-xl border-0 py-2 pl-10 pr-4 text-slate-900 ring-1 ring-inset ring-slate-200 placeholder:text-slate-400 focus:ring-2 focus:ring-inset focus:ring-medical-blue sm:text-sm sm:leading-6 dark:bg-slate-900 dark:text-white dark:ring-slate-700"
            placeholder="Search reports..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
          />
        </div>
      </div>

      <div className="glass rounded-2xl overflow-hidden shadow-sm border border-slate-200 dark:border-slate-800">
        {loading ? (
          <div className="p-12 flex justify-center">
            <Loader2 className="h-8 w-8 text-medical-blue animate-spin" />
          </div>
        ) : error ? (
          <div className="p-12 text-center text-red-500 flex flex-col items-center">
            <AlertCircle className="h-8 w-8 mb-2" />
            <p>{error}</p>
          </div>
        ) : filteredReports.length === 0 ? (
          <div className="p-12 text-center text-slate-500">
            No reports found.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm text-left">
              <thead className="bg-slate-50 dark:bg-slate-900 border-b border-slate-200 dark:border-slate-800">
                <tr>
                  <th className="px-6 py-4 text-left text-xs font-semibold text-slate-500 uppercase tracking-wider">Report Name</th>
                  <th className="px-6 py-4 text-left text-xs font-semibold text-slate-500 uppercase tracking-wider">Date</th>
                  <th className="px-6 py-4 text-left text-xs font-semibold text-slate-500 uppercase tracking-wider">Source</th>
                  <th className="px-6 py-4 text-left text-xs font-semibold text-slate-500 uppercase tracking-wider">Total Items</th>
                  <th className="px-6 py-4 text-left text-xs font-semibold text-slate-500 uppercase tracking-wider">Critical</th>
                  <th className="px-6 py-4 text-right text-xs font-semibold text-slate-500 uppercase tracking-wider">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-200 dark:divide-slate-800 bg-white dark:bg-slate-950/50">
                {filteredReports.map((report) => (
                  <tr key={report.id} className="hover:bg-slate-50 dark:hover:bg-slate-900/50 transition-colors">
                    <td className="px-6 py-4 font-medium text-slate-900 dark:text-white flex items-center gap-3">
                      <div className="bg-blue-50 dark:bg-blue-900/20 p-2 rounded-lg text-medical-blue">
                        <FileText className="h-4 w-4" />
                      </div>
                      {report.title}
                    </td>
                    <td className="px-6 py-4 text-slate-500">
                      {new Date(report.created_at).toLocaleDateString()}
                    </td>
                    <td className="px-6 py-4 text-slate-500 capitalize">
                      {report.source_type}
                    </td>
                    <td className="px-6 py-4 text-slate-500">
                      {report.total_medicines}
                    </td>
                    <td className="px-6 py-4">
                      {report.critical_count > 0 ? (
                        <PriorityBadge priority="critical" />
                      ) : (
                        <span className="text-slate-400">-</span>
                      )}
                    </td>
                    <td className="px-6 py-4 text-right">
                      <Link 
                        href={`/report/${report.id}`}
                        className="text-medical-blue hover:opacity-80 font-medium text-sm"
                      >
                        View Report
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
