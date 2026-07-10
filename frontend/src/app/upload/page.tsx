"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { api, uploadApi } from "@/lib/api";
import { useReportStore } from "@/stores/reportStore";
import { useSettingsStore } from "@/stores/settingsStore";
import DropZone from "@/components/upload/DropZone";
import ProgressIndicator from "@/components/upload/ProgressIndicator";
import { AlertCircle } from "lucide-react";

export default function UploadPage() {
  const router = useRouter();
  const { setReport, setLoading: setStoreLoading, setError: setStoreError } = useReportStore();
  const { settings } = useSettingsStore();
  
  const [file, setFile] = useState<File | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [status, setStatus] = useState("");
  const [error, setError] = useState<string | null>(null);

  const handleFileSelect = (selectedFile: File | null) => {
    setFile(selectedFile);
    setError(null);
  };

  const handleUpload = async () => {
    if (!file) return;

    setIsUploading(true);
    setProgress(10);
    setStatus("Uploading file...");
    setError(null);
    setStoreError(null);

    const formData = new FormData();
    formData.append("file", file);

    // Simulate progress for UI purposes (backend doesn't stream progress yet)
    const progressInterval = setInterval(() => {
      setProgress((prev) => {
        if (prev >= 90) return prev;
        return prev + 5;
      });
    }, 1000);

    try {

      setStatus("Running AI analysis...");
      
      const response = await uploadApi.post(`/upload?min_stock=${settings.default_min_stock}`, formData);

      clearInterval(progressInterval);
      setProgress(100);
      setStatus("Report generated successfully!");

      const report = response.data;
      setReport(report);

      // Navigate to report page
      setTimeout(() => {
        router.push(`/report/${report.id}`);
      }, 500);

    } catch (err: any) {
      console.error(err);
      clearInterval(progressInterval);
      setIsUploading(false);
      setProgress(0);
      setStatus("");

      const errorMessage = err.response?.data?.detail || "An error occurred during file processing.";
      setError(errorMessage);
    }
  };

  return (
    <div className="max-w-4xl mx-auto space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-500">
      <div className="text-center space-y-2">
        <h1 className="text-3xl font-bold tracking-tight text-slate-900 dark:text-white">
          Generate Shortage Report
        </h1>
        <p className="text-slate-500 dark:text-slate-400">
          Upload a screenshot from Titan, or import an Excel/CSV file to instantly generate your report.
        </p>
      </div>

      <div className="glass rounded-3xl p-6 sm:p-10 shadow-sm border border-slate-200 dark:border-slate-800">
        {!isUploading ? (
          <div className="space-y-6">
            <DropZone onFileSelect={handleFileSelect} selectedFile={file} />
            
            {error && (
              <div className="p-4 bg-red-50 dark:bg-red-900/20 text-red-600 dark:text-red-400 rounded-xl flex items-start gap-3 border border-red-100 dark:border-red-900/50">
                <AlertCircle className="h-5 w-5 shrink-0 mt-0.5" />
                <p className="text-sm">{error}</p>
              </div>
            )}

            <div className="flex justify-end">
              <button
                onClick={handleUpload}
                disabled={!file}
                className="rounded-xl bg-medical-blue px-8 py-3.5 text-sm font-semibold text-white shadow-sm hover:bg-medical-blue/90 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-medical-blue disabled:opacity-50 disabled:cursor-not-allowed transition-all"
              >
                Analyze File
              </button>
            </div>
          </div>
        ) : (
          <ProgressIndicator progress={progress} status={status} />
        )}
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-3 gap-6 pt-8 border-t border-slate-200 dark:border-slate-800">
        <div className="text-center space-y-2">
          <div className="bg-blue-50 dark:bg-blue-900/20 w-12 h-12 rounded-full flex items-center justify-center mx-auto text-medical-blue font-bold">1</div>
          <h3 className="font-medium text-slate-900 dark:text-white">Upload</h3>
          <p className="text-sm text-slate-500">Screenshot, PDF, or Excel</p>
        </div>
        <div className="text-center space-y-2">
          <div className="bg-blue-50 dark:bg-blue-900/20 w-12 h-12 rounded-full flex items-center justify-center mx-auto text-medical-blue font-bold">2</div>
          <h3 className="font-medium text-slate-900 dark:text-white">AI Analysis</h3>
          <p className="text-sm text-slate-500">Extracts names & stock levels</p>
        </div>
        <div className="text-center space-y-2">
          <div className="bg-blue-50 dark:bg-blue-900/20 w-12 h-12 rounded-full flex items-center justify-center mx-auto text-medical-blue font-bold">3</div>
          <h3 className="font-medium text-slate-900 dark:text-white">Export</h3>
          <p className="text-sm text-slate-500">Download formatted report</p>
        </div>
      </div>
    </div>
  );
}
