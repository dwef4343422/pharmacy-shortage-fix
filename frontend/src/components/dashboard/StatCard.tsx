"use client";

import { ReactNode } from "react";
import { ArrowDownIcon, ArrowUpIcon } from "lucide-react";

interface StatCardProps {
  title: string;
  value: string | number;
  icon: ReactNode;
  trend?: string;
  trendUp?: boolean;
  color?: "default" | "warning" | "critical";
}

export default function StatCard({ title, value, icon, trend, trendUp, color = "default" }: StatCardProps) {
  const colorStyles = {
    default: "bg-medical-blue/10 text-medical-blue dark:bg-medical-blue/20 dark:text-blue-400",
    warning: "bg-yellow-100/50 text-yellow-700 dark:bg-yellow-500/20 dark:text-yellow-400",
    critical: "bg-red-100/50 text-red-600 dark:bg-red-500/20 dark:text-red-400",
  };

  const iconBg = colorStyles[color];

  return (
    <div className="glass rounded-2xl p-5 hover:-translate-y-1 transition-transform duration-300">
      <div className="flex items-center justify-between">
        <p className="text-sm font-medium text-slate-500 dark:text-slate-400">{title}</p>
        <div className={`p-2 rounded-lg ${iconBg}`}>
          {icon}
        </div>
      </div>
      
      <div className="mt-4 flex items-baseline gap-2">
        <h3 className="text-2xl font-bold text-slate-900 dark:text-white">{value}</h3>
      </div>
      
      {trend && (
        <div className="mt-2 flex items-center text-xs">
          {trendUp ? (
            <ArrowUpIcon className={`mr-1 h-3 w-3 ${color === 'warning' || color === 'critical' ? 'text-red-500' : 'text-emerald-500'}`} />
          ) : (
            <ArrowDownIcon className={`mr-1 h-3 w-3 ${color === 'warning' || color === 'critical' ? 'text-emerald-500' : 'text-red-500'}`} />
          )}
          <span className="text-slate-500 dark:text-slate-400">{trend}</span>
        </div>
      )}
    </div>
  );
}
