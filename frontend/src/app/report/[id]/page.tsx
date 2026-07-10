"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { api } from "@/lib/api";
import { useReportStore, Medicine } from "@/stores/reportStore";
import ShortageTable from "@/components/report/ShortageTable";
import SearchBar from "@/components/report/SearchBar";
import FilterChips from "@/components/report/FilterChips";
import ExportToolbar from "@/components/report/ExportToolbar";
import StatCard from "@/components/dashboard/StatCard";
import { AlertTriangle, Box, FileText, ArrowLeft, Loader2, Activity } from "lucide-react";

export default function ReportPage() {
  const params = useParams();
  const router = useRouter();
  const { currentReport, setReport, isLoading, setLoading, error, setError } = useReportStore();
  
  const [searchQuery, setSearchQuery] = useState("");
  const [activeFilter, setActiveFilter] = useState("all");
  const [sortConfig, setSortConfig] = useState<{ key: keyof Medicine, direction: 'asc' | 'desc' }>({
    key: 'priority', // Default sort
    direction: 'asc'
  });

  useEffect(() => {
    const fetchReport = async () => {
      if (!params.id) return;
      
      // If we already have this report in the store, don't refetch
      if (currentReport?.id === params.id) return;

      setLoading(true);
      try {
        const response = await api.get(`/reports/${params.id}`);
        setReport(response.data);
      } catch (err: any) {
        console.error("Failed to fetch report:", err);
        setError(err.response?.data?.detail || "Failed to load report");
      } finally {
        setLoading(false);
      }
    };

    fetchReport();
  }, [params.id, currentReport?.id, setLoading, setReport, setError]);

  if (isLoading) {
    return (
      <div className="h-[60vh] flex flex-col items-center justify-center">
        <Loader2 className="h-8 w-8 text-medical-blue animate-spin mb-4" />
        <p className="text-slate-500">Loading report data...</p>
      </div>
    );
  }

  if (error || !currentReport) {
    return (
      <div className="h-[60vh] flex flex-col items-center justify-center text-center">
        <div className="bg-red-50 p-4 rounded-full mb-4">
          <AlertTriangle className="h-8 w-8 text-red-500" />
        </div>
        <h2 className="text-xl font-bold text-slate-900 dark:text-white mb-2">Report Not Found</h2>
        <p className="text-slate-500 mb-6 max-w-md">{error || "The requested report could not be found or you don't have access to it."}</p>
        <button 
          onClick={() => router.push('/')}
          className="bg-medical-blue text-white px-6 py-2 rounded-xl hover:bg-medical-blue/90 transition-colors"
        >
          Return to Dashboard
        </button>
      </div>
    );
  }

  // Filter and Sort Logic
  let processedMedicines = [...currentReport.medicines];

  // 1. Filter by Priority
  if (activeFilter !== 'all') {
    processedMedicines = processedMedicines.filter(m => m.priority === activeFilter);
  }

  // 2. Filter by Search Query
  if (searchQuery) {
    const query = searchQuery.toLowerCase();
    processedMedicines = processedMedicines.filter(m => 
      m.name.toLowerCase().includes(query) || 
      (m.name_arabic && m.name_arabic.toLowerCase().includes(query))
    );
  }

  // 3. Sort
  processedMedicines.sort((a, b) => {
    let valA = a[sortConfig.key];
    let valB = b[sortConfig.key];
    
    // Special handling for priority sorting
    if (sortConfig.key === 'priority') {
      const order = { critical: 0, high: 1, medium: 2, safe: 3 };
      valA = order[a.priority];
      valB = order[b.priority];
    }
    
    if (valA === null) return 1;
    if (valB === null) return -1;
    
    if (valA < valB) return sortConfig.direction === 'asc' ? -1 : 1;
    if (valA > valB) return sortConfig.direction === 'asc' ? 1 : -1;
    return 0;
  });

  // Calculate counts for filters
  const counts = {
    all: currentReport.medicines.length,
    critical: currentReport.medicines.filter(m => m.priority === 'critical').length,
    high: currentReport.medicines.filter(m => m.priority === 'high').length,
    medium: currentReport.medicines.filter(m => m.priority === 'medium').length,
    safe: currentReport.medicines.filter(m => m.priority === 'safe').length,
  };

  return (
    <div className="space-y-6 animate-in fade-in duration-500">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <button 
            onClick={() => router.push('/history')}
            className="text-slate-500 hover:text-slate-900 dark:hover:text-white flex items-center gap-1 text-sm font-medium mb-2 transition-colors"
          >
            <ArrowLeft className="h-4 w-4" /> Back to History
          </button>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-white flex items-center gap-2">
            {currentReport.title}
          </h1>
          <p className="text-slate-500 text-sm mt-1">
            Generated on {new Date(currentReport.created_at).toLocaleString()} • Source: {currentReport.source_type}
          </p>
        </div>
        <ExportToolbar reportId={currentReport.id} />
      </div>

      {/* Stats Summary */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard 
          title="Total Required" 
          value={currentReport.total_required} 
          icon={<Box className="h-5 w-5" />} 
        />
        <StatCard 
          title="Critical Items" 
          value={currentReport.critical_count} 
          icon={<AlertTriangle className="h-5 w-5" />} 
          color="critical"
        />
        <StatCard 
          title="Below Minimum" 
          value={currentReport.below_minimum_count} 
          icon={<FileText className="h-5 w-5" />} 
          color="warning"
        />
        <StatCard 
          title="Total Medicines" 
          value={currentReport.total_medicines} 
          icon={<Activity className="h-5 w-5" />} 
        />
      </div>

      {/* Toolbar */}
      <div className="glass rounded-2xl p-4 flex flex-col md:flex-row justify-between items-center gap-4">
        <FilterChips counts={counts} activeFilter={activeFilter} onFilterChange={setActiveFilter} />
        <div className="w-full md:w-auto">
          <SearchBar onSearch={setSearchQuery} />
        </div>
      </div>

      {/* Main Table */}
      <div className="glass rounded-2xl overflow-hidden shadow-sm border border-slate-200 dark:border-slate-800">
        <ShortageTable 
          medicines={processedMedicines} 
          sortConfig={sortConfig}
          onSort={(key) => {
            setSortConfig(current => ({
              key,
              direction: current.key === key && current.direction === 'asc' ? 'desc' : 'asc'
            }));
          }}
          reportId={currentReport.id}
        />
      </div>
    </div>
  );
}
