"use client";

interface FilterChipsProps {
  counts: {
    all: number;
    critical: number;
    high: number;
    medium: number;
    safe: number;
  };
  activeFilter: string;
  onFilterChange: (filter: string) => void;
}

export default function FilterChips({ counts, activeFilter, onFilterChange }: FilterChipsProps) {
  const filters = [
    { id: "all", label: "All", count: counts.all, color: "bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-300", activeColor: "bg-slate-800 text-white dark:bg-slate-200 dark:text-slate-900" },
    { id: "critical", label: "Critical", count: counts.critical, color: "bg-red-50 text-red-600 dark:bg-red-500/10 dark:text-red-400", activeColor: "bg-red-500 text-white" },
    { id: "high", label: "High", count: counts.high, color: "bg-orange-50 text-orange-600 dark:bg-orange-500/10 dark:text-orange-400", activeColor: "bg-orange-500 text-white" },
    { id: "medium", label: "Medium", count: counts.medium, color: "bg-yellow-50 text-yellow-600 dark:bg-yellow-500/10 dark:text-yellow-400", activeColor: "bg-yellow-500 text-white" },
    { id: "safe", label: "Safe", count: counts.safe, color: "bg-emerald-50 text-emerald-600 dark:bg-emerald-500/10 dark:text-emerald-400", activeColor: "bg-emerald-500 text-white" },
  ];

  return (
    <div className="flex items-center gap-2 overflow-x-auto pb-2 md:pb-0 hide-scrollbar">
      {filters.map((filter) => {
        const isActive = activeFilter === filter.id;
        
        return (
          <button
            key={filter.id}
            onClick={() => onFilterChange(filter.id)}
            className={`
              flex items-center gap-2 whitespace-nowrap px-4 py-2 rounded-full text-sm font-medium transition-colors border border-transparent
              ${isActive ? filter.activeColor : `${filter.color} hover:border-slate-300 dark:hover:border-slate-600`}
            `}
          >
            {filter.label}
            <span className={`
              px-2 py-0.5 rounded-full text-xs
              ${isActive ? 'bg-white/20' : 'bg-white/50 dark:bg-black/20'}
            `}>
              {filter.count}
            </span>
          </button>
        );
      })}
    </div>
  );
}
