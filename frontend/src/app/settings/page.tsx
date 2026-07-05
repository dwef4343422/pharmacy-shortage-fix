"use client";

import { useEffect, useState } from "react";
import { useSettingsStore } from "@/stores/settingsStore";
import { Check, Settings as SettingsIcon } from "lucide-react";

export default function SettingsPage() {
  const { settings, updateSettings } = useSettingsStore();
  const [mounted, setMounted] = useState(false);
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  const handleSave = () => {
    setSaved(true);
    setTimeout(() => setSaved(false), 3000);
  };

  if (!mounted) return null;

  return (
    <div className="max-w-3xl mx-auto space-y-8 animate-in fade-in duration-500">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-white flex items-center gap-2">
            <SettingsIcon className="h-6 w-6" />
            Settings
          </h1>
          <p className="text-slate-500 text-sm mt-1">
            Manage your preferences and application defaults.
          </p>
        </div>
        <button
          onClick={handleSave}
          className="bg-medical-blue hover:bg-medical-blue/90 text-white px-6 py-2 rounded-xl text-sm font-medium transition-colors flex items-center gap-2"
        >
          {saved ? <><Check className="h-4 w-4" /> Saved</> : "Save Changes"}
        </button>
      </div>

      <div className="glass rounded-3xl p-6 sm:p-8 space-y-8 border border-slate-200 dark:border-slate-800">
        
        {/* General Settings */}
        <section>
          <h2 className="text-lg font-semibold text-slate-900 dark:text-white mb-4">General</h2>
          <div className="space-y-4">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 py-3 border-b border-slate-100 dark:border-slate-800">
              <div>
                <label className="font-medium text-slate-900 dark:text-white">Default Minimum Stock</label>
                <p className="text-sm text-slate-500">The threshold below which a medicine is considered in shortage.</p>
              </div>
              <input 
                type="number" 
                min="1"
                className="w-24 px-3 py-2 border border-slate-200 dark:border-slate-700 rounded-xl bg-white dark:bg-slate-900 text-slate-900 dark:text-white focus:ring-2 focus:ring-medical-blue outline-none"
                value={settings.default_min_stock}
                onChange={(e) => updateSettings({ default_min_stock: parseInt(e.target.value) || 10 })}
              />
            </div>

            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 py-3 border-b border-slate-100 dark:border-slate-800">
              <div>
                <label className="font-medium text-slate-900 dark:text-white">Default Export Format</label>
                <p className="text-sm text-slate-500">Preferred format when downloading reports.</p>
              </div>
              <select 
                className="w-full sm:w-48 px-3 py-2 border border-slate-200 dark:border-slate-700 rounded-xl bg-white dark:bg-slate-900 text-slate-900 dark:text-white focus:ring-2 focus:ring-medical-blue outline-none"
                value={settings.export_format}
                onChange={(e) => updateSettings({ export_format: e.target.value as any })}
              >
                <option value="excel">Excel (.xlsx)</option>
                <option value="pdf">PDF</option>
                <option value="csv">CSV</option>
              </select>
            </div>
          </div>
        </section>

        {/* Appearance & OCR */}
        <section>
          <h2 className="text-lg font-semibold text-slate-900 dark:text-white mb-4">Appearance & Analysis</h2>
          <div className="space-y-4">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 py-3 border-b border-slate-100 dark:border-slate-800">
              <div>
                <label className="font-medium text-slate-900 dark:text-white">Theme</label>
                <p className="text-sm text-slate-500">Select your preferred color scheme.</p>
              </div>
              <select 
                className="w-full sm:w-48 px-3 py-2 border border-slate-200 dark:border-slate-700 rounded-xl bg-white dark:bg-slate-900 text-slate-900 dark:text-white focus:ring-2 focus:ring-medical-blue outline-none"
                value={settings.theme}
                onChange={(e) => updateSettings({ theme: e.target.value as any })}
              >
                <option value="light">Light</option>
                <option value="dark">Dark</option>
                <option value="system">System Default</option>
              </select>
            </div>

            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 py-3">
              <div>
                <label className="font-medium text-slate-900 dark:text-white">OCR Sensitivity</label>
                <p className="text-sm text-slate-500">How strict the AI should be when reading text.</p>
              </div>
              <select 
                className="w-full sm:w-48 px-3 py-2 border border-slate-200 dark:border-slate-700 rounded-xl bg-white dark:bg-slate-900 text-slate-900 dark:text-white focus:ring-2 focus:ring-medical-blue outline-none"
                value={settings.ocr_sensitivity}
                onChange={(e) => updateSettings({ ocr_sensitivity: e.target.value as any })}
              >
                <option value="low">Low (Captures more)</option>
                <option value="medium">Medium (Balanced)</option>
                <option value="high">High (Strict)</option>
              </select>
            </div>
          </div>
        </section>
        
      </div>
    </div>
  );
}
