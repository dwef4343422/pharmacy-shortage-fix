import Link from "next/link";
import { Activity, AlertTriangle, ArrowRight, FileText, Upload } from "lucide-react";
import StatCard from "@/components/dashboard/StatCard";
import RecentActivity from "@/components/dashboard/RecentActivity";

export default function DashboardPage() {
  return (
    <div className="space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-500">
      {/* Hero / Welcome */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 glass p-6 rounded-2xl">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-white">
            Dashboard
          </h1>
          <p className="text-slate-500 dark:text-slate-400 mt-1">
            Welcome back to Smart Shortage Manager.
          </p>
        </div>
        <div className="flex items-center gap-3">
          <Link
            href="/upload"
            className="inline-flex items-center justify-center rounded-xl bg-medical-blue px-6 py-3 text-sm font-medium text-white shadow hover:bg-medical-blue/90 transition-all active:scale-95 gap-2"
          >
            <Upload className="h-4 w-4" />
            New Report
          </Link>
        </div>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          title="Total Medicines"
          value="1,248"
          icon={<Activity className="h-5 w-5" />}
          trend="+12 this week"
          trendUp={true}
        />
        <StatCard
          title="Below Minimum"
          value="42"
          icon={<AlertTriangle className="h-5 w-5" />}
          trend="-5 since yesterday"
          trendUp={true} // fewer shortages is good
          color="warning"
        />
        <StatCard
          title="Critical Items"
          value="8"
          icon={<AlertTriangle className="h-5 w-5" />}
          trend="+2 since yesterday"
          trendUp={false} // more critical is bad
          color="critical"
        />
        <StatCard
          title="Reports Generated"
          value="24"
          icon={<FileText className="h-5 w-5" />}
          trend="+4 this month"
          trendUp={true}
        />
      </div>

      {/* Main Content Area */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        <div className="lg:col-span-2 space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-semibold text-slate-900 dark:text-white">
              Recent Reports
            </h2>
            <Link href="/history" className="text-sm text-medical-blue hover:underline flex items-center gap-1">
              View all <ArrowRight className="h-3 w-3" />
            </Link>
          </div>
          <div className="glass rounded-2xl p-1">
            <RecentActivity />
          </div>
        </div>

        <div className="space-y-4">
          <h2 className="text-lg font-semibold text-slate-900 dark:text-white">
            Quick Actions
          </h2>
          <div className="glass rounded-2xl p-4 flex flex-col gap-3">
            <Link href="/upload" className="flex items-center p-3 rounded-xl hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors group">
              <div className="bg-blue-100 dark:bg-blue-900/30 p-2 rounded-lg text-medical-blue mr-4 group-hover:scale-110 transition-transform">
                <Upload className="h-5 w-5" />
              </div>
              <div>
                <div className="font-medium">Upload Screenshot</div>
                <div className="text-xs text-slate-500">Run OCR analysis on Titan</div>
              </div>
            </Link>
            <Link href="/upload" className="flex items-center p-3 rounded-xl hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors group">
              <div className="bg-emerald-100 dark:bg-emerald-900/30 p-2 rounded-lg text-medical-green mr-4 group-hover:scale-110 transition-transform">
                <FileText className="h-5 w-5" />
              </div>
              <div>
                <div className="font-medium">Import Excel/CSV</div>
                <div className="text-xs text-slate-500">Process exported data</div>
              </div>
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}
