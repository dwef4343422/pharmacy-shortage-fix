"use client";

interface PriorityBadgeProps {
  priority: 'critical' | 'high' | 'medium' | 'safe';
}

export default function PriorityBadge({ priority }: PriorityBadgeProps) {
  const config = {
    critical: { color: "bg-red-100 text-red-700 dark:bg-red-500/20 dark:text-red-400", label: "Critical", pulse: true },
    high: { color: "bg-orange-100 text-orange-700 dark:bg-orange-500/20 dark:text-orange-400", label: "High", pulse: false },
    medium: { color: "bg-yellow-100 text-yellow-700 dark:bg-yellow-500/20 dark:text-yellow-400", label: "Medium", pulse: false },
    safe: { color: "bg-emerald-100 text-emerald-700 dark:bg-emerald-500/20 dark:text-emerald-400", label: "Safe", pulse: false },
  };

  const { color, label, pulse } = config[priority] || config.safe;

  return (
    <div className="flex items-center">
      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${color}`}>
        {pulse && (
          <span className="flex h-2 w-2 mr-1.5 relative">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-red-400 opacity-75"></span>
            <span className="relative inline-flex rounded-full h-2 w-2 bg-red-500"></span>
          </span>
        )}
        {label}
      </span>
    </div>
  );
}
