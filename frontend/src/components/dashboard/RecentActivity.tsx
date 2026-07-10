"use client";

import { FileText, MoreVertical, Download } from "lucide-react";

export default function RecentActivity() {
  // Mock data for Phase 1
  const activities = [
    { id: 1, title: "Morning Shortage Report", type: "screenshot", items: 42, critical: 5, date: "Today, 09:30 AM", status: "completed" },
    { id: 2, title: "Titan Export Analysis", type: "excel", items: 156, critical: 12, date: "Yesterday, 04:15 PM", status: "completed" },
    { id: 3, title: "Quick Check", type: "screenshot", items: 8, critical: 0, date: "Jul 02, 11:20 AM", status: "completed" },
    { id: 4, title: "Monthly Inventory", type: "pdf", items: 845, critical: 34, date: "Jul 01, 10:00 AM", status: "completed" },
  ];

  return (
    <div className="overflow-hidden">
      <ul role="list" className="divide-y divide-slate-100 dark:divide-slate-800">
        {activities.map((activity) => (
          <li key={activity.id} className="flex items-center justify-between p-4 hover:bg-slate-50 dark:hover:bg-slate-800/50 transition-colors">
            <div className="flex items-center gap-4">
              <div className="bg-blue-50 dark:bg-blue-900/20 p-2.5 rounded-xl text-medical-blue">
                <FileText className="h-5 w-5" />
              </div>
              <div>
                <p className="text-sm font-medium text-slate-900 dark:text-white">
                  {activity.title}
                </p>
                <div className="flex items-center gap-2 mt-1">
                  <span className="text-xs text-slate-500 dark:text-slate-400">
                    {activity.date}
                  </span>
                  <span className="text-xs text-slate-300 dark:text-slate-600">•</span>
                  <span className="text-xs text-slate-500 dark:text-slate-400 capitalize">
                    {activity.type}
                  </span>
                </div>
              </div>
            </div>
            <div className="flex items-center gap-4">
              <div className="hidden sm:flex flex-col items-end">
                <p className="text-sm font-medium text-slate-900 dark:text-white">{activity.items} items</p>
                <p className="text-xs text-medical-critical dark:text-red-400">{activity.critical} critical</p>
              </div>
              <button className="p-2 text-slate-400 hover:text-medical-blue transition-colors rounded-lg hover:bg-blue-50 dark:hover:bg-blue-900/20">
                <Download className="h-4 w-4" />
              </button>
            </div>
          </li>
        ))}
      </ul>
    </div>
  );
}
