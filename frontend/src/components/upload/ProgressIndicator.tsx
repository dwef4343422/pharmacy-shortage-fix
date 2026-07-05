"use client";

import { Loader2 } from "lucide-react";

interface ProgressIndicatorProps {
  progress: number;
  status: string;
}

export default function ProgressIndicator({ progress, status }: ProgressIndicatorProps) {
  return (
    <div className="py-12 flex flex-col items-center justify-center space-y-8 animate-in fade-in duration-500">
      <div className="relative">
        {/* Glowing background effect */}
        <div className="absolute inset-0 bg-medical-blue/20 blur-xl rounded-full scale-150 animate-pulse"></div>
        
        <div className="relative bg-white dark:bg-slate-900 p-4 rounded-2xl shadow-xl border border-slate-100 dark:border-slate-800">
          <Loader2 className="h-12 w-12 text-medical-blue animate-spin" />
        </div>
      </div>

      <div className="text-center space-y-4 w-full max-w-md">
        <h3 className="text-xl font-semibold text-slate-900 dark:text-white">
          {status}
        </h3>
        
        <div className="relative h-2 w-full overflow-hidden rounded-full bg-slate-100 dark:bg-slate-800">
          <div 
            className="absolute h-full bg-medical-blue transition-all duration-500 ease-out"
            style={{ width: `${progress}%` }}
          >
            {/* Shimmer effect */}
            <div className="absolute top-0 right-0 bottom-0 left-0 bg-gradient-to-r from-transparent via-white/30 to-transparent -translate-x-full animate-[shimmer_2s_infinite]"></div>
          </div>
        </div>
        
        <p className="text-sm text-slate-500 dark:text-slate-400 font-medium">
          {progress}% Complete
        </p>
      </div>

      <style jsx>{`
        @keyframes shimmer {
          100% {
            transform: translateX(100%);
          }
        }
      `}</style>
    </div>
  );
}
