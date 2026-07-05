"use client";

import { useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import { UploadCloud, File, X, Image as ImageIcon, FileSpreadsheet } from 'lucide-react';

interface DropZoneProps {
  onFileSelect: (file: File | null) => void;
  selectedFile: File | null;
}

export default function DropZone({ onFileSelect, selectedFile }: DropZoneProps) {
  const onDrop = useCallback((acceptedFiles: File[]) => {
    if (acceptedFiles.length > 0) {
      onFileSelect(acceptedFiles[0]);
    }
  }, [onFileSelect]);

  const { getRootProps, getInputProps, isDragActive, isDragReject } = useDropzone({
    onDrop,
    accept: {
      'image/*': ['.png', '.jpg', '.jpeg', '.bmp'],
      'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': ['.xlsx'],
      'application/vnd.ms-excel': ['.xls'],
      'text/csv': ['.csv'],
      'application/pdf': ['.pdf'],
    },
    maxFiles: 1,
    maxSize: 10 * 1024 * 1024, // 10MB
  });

  const removeFile = (e: React.MouseEvent) => {
    e.stopPropagation();
    onFileSelect(null);
  };

  const getFileIcon = (file: File) => {
    if (file.type.startsWith('image/')) return <ImageIcon className="h-8 w-8 text-blue-500" />;
    if (file.type.includes('excel') || file.type.includes('spreadsheet') || file.type.includes('csv')) {
      return <FileSpreadsheet className="h-8 w-8 text-green-500" />;
    }
    return <File className="h-8 w-8 text-slate-500" />;
  };

  return (
    <div>
      {selectedFile ? (
        <div className="relative overflow-hidden rounded-2xl border-2 border-medical-blue/20 bg-blue-50/50 dark:bg-blue-900/10 p-6 transition-all">
          <div className="flex items-center gap-4">
            <div className="bg-white dark:bg-slate-800 p-3 rounded-xl shadow-sm">
              {getFileIcon(selectedFile)}
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-semibold text-slate-900 dark:text-white truncate">
                {selectedFile.name}
              </p>
              <p className="text-xs text-slate-500 mt-1">
                {(selectedFile.size / (1024 * 1024)).toFixed(2)} MB
              </p>
            </div>
            <button
              onClick={removeFile}
              className="p-2 text-slate-400 hover:text-red-500 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-full transition-colors"
            >
              <X className="h-5 w-5" />
            </button>
          </div>
        </div>
      ) : (
        <div
          {...getRootProps()}
          className={`relative cursor-pointer overflow-hidden rounded-2xl border-2 border-dashed p-12 transition-all text-center
            ${isDragActive 
              ? 'border-medical-blue bg-blue-50 dark:bg-blue-900/20 scale-[0.99]' 
              : isDragReject
                ? 'border-red-400 bg-red-50 dark:bg-red-900/20'
                : 'border-slate-300 dark:border-slate-700 hover:border-medical-blue/50 hover:bg-slate-50 dark:hover:bg-slate-800/50'
            }`}
        >
          <input {...getInputProps()} />
          
          <div className="flex flex-col items-center justify-center space-y-4">
            <div className={`p-4 rounded-full ${isDragActive ? 'bg-medical-blue text-white' : 'bg-slate-100 dark:bg-slate-800 text-slate-400'} transition-colors duration-300`}>
              <UploadCloud className="h-10 w-10" />
            </div>
            
            <div>
              <p className="text-lg font-medium text-slate-900 dark:text-white">
                {isDragActive ? "Drop file here to analyze" : "Click or drag file to this area"}
              </p>
              <p className="text-sm text-slate-500 mt-2 max-w-xs mx-auto">
                Support for Titan screenshots, Excel, CSV, or PDF files. Maximum file size 10MB.
              </p>
            </div>

            <div className="flex gap-2 mt-4">
              <span className="inline-flex items-center rounded-full bg-slate-100 dark:bg-slate-800 px-2.5 py-0.5 text-xs font-medium text-slate-600 dark:text-slate-300">
                PNG/JPG
              </span>
              <span className="inline-flex items-center rounded-full bg-emerald-50 dark:bg-emerald-900/20 px-2.5 py-0.5 text-xs font-medium text-emerald-600 dark:text-emerald-400">
                XLSX/CSV
              </span>
              <span className="inline-flex items-center rounded-full bg-red-50 dark:bg-red-900/20 px-2.5 py-0.5 text-xs font-medium text-red-600 dark:text-red-400">
                PDF
              </span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
