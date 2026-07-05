"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Activity, Menu, Moon, Sun, User } from "lucide-react";
import { useSettingsStore } from "@/stores/settingsStore";
import { useEffect, useState } from "react";

export default function Navbar() {
  const pathname = usePathname();
  const { settings, updateSettings } = useSettingsStore();
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
    if (settings.theme === 'dark' || (settings.theme === 'system' && window.matchMedia('(prefers-color-scheme: dark)').matches)) {
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
    }
  }, [settings.theme]);

  const toggleTheme = () => {
    const newTheme = settings.theme === 'dark' ? 'light' : 'dark';
    updateSettings({ theme: newTheme });
  };

  return (
    <header className="sticky top-0 z-50 w-full border-b border-border/40 bg-white/95 dark:bg-slate-950/95 backdrop-blur supports-[backdrop-filter]:bg-white/60">
      <div className="flex h-16 items-center px-4 md:px-6">
        <button className="mr-4 md:hidden p-2 text-slate-500 hover:text-slate-900 dark:hover:text-white">
          <Menu className="h-5 w-5" />
        </button>
        
        <Link href="/" className="flex items-center gap-2 mr-6">
          <div className="bg-medical-blue p-1.5 rounded-lg text-white">
            <Activity className="h-5 w-5" />
          </div>
          <span className="font-bold hidden sm:inline-block text-slate-900 dark:text-white">
            Smart Shortage Manager
          </span>
        </Link>

        <nav className="hidden md:flex items-center gap-6 text-sm font-medium">
          <Link href="/" className={`transition-colors hover:text-foreground/80 ${pathname === '/' ? 'text-foreground' : 'text-foreground/60'}`}>Dashboard</Link>
          <Link href="/upload" className={`transition-colors hover:text-foreground/80 ${pathname.startsWith('/upload') ? 'text-foreground' : 'text-foreground/60'}`}>Upload</Link>
          <Link href="/history" className={`transition-colors hover:text-foreground/80 ${pathname.startsWith('/history') ? 'text-foreground' : 'text-foreground/60'}`}>History</Link>
          <Link href="/settings" className={`transition-colors hover:text-foreground/80 ${pathname.startsWith('/settings') ? 'text-foreground' : 'text-foreground/60'}`}>Settings</Link>
        </nav>

        <div className="ml-auto flex items-center space-x-4">
          <button onClick={toggleTheme} className="p-2 rounded-full hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors">
            {mounted && settings.theme === 'dark' ? <Sun className="h-5 w-5" /> : <Moon className="h-5 w-5" />}
          </button>
          
          <div className="h-8 w-8 rounded-full bg-slate-200 dark:bg-slate-800 flex items-center justify-center">
            <User className="h-4 w-4 text-slate-500 dark:text-slate-400" />
          </div>
        </div>
      </div>
    </header>
  );
}
