"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard,
  CreditCard,
  Bot,
  AlertTriangle,
  Users,
  Zap,
} from "lucide-react";

const navItems = [
  { href: "/", label: "Dashboard", icon: LayoutDashboard },
  { href: "/failed-payments", label: "Failed Payments", icon: CreditCard },
  { href: "/ai-log", label: "AI Decision Log", icon: Bot },
  { href: "/escalations", label: "Escalations", icon: AlertTriangle },
  { href: "/customers", label: "Customers", icon: Users },
];

export function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="w-64 flex-shrink-0 bg-gray-900 border-r border-gray-800/60 flex flex-col">
      {/* Logo */}
      <div className="px-6 py-5 border-b border-gray-800/60">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center">
            <Zap className="w-4 h-4 text-white" />
          </div>
          <div>
            <h1 className="text-sm font-bold text-white leading-tight">AI Collections</h1>
            <p className="text-xs text-gray-500">Paytm Agent</p>
          </div>
        </div>
      </div>

      {/* Live indicator */}
      <div className="px-6 py-3 border-b border-gray-800/60">
        <div className="flex items-center gap-2">
          <span className="relative flex h-2 w-2">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75" />
            <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500" />
          </span>
          <span className="text-xs text-emerald-400 font-medium">Agent Active</span>
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 px-3 py-4 space-y-1">
        {navItems.map(({ href, label, icon: Icon }) => {
          const isActive = pathname === href;
          return (
            <Link
              key={href}
              href={href}
              className={`flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all duration-200 ${
                isActive
                  ? "bg-blue-500/15 text-blue-400 border border-blue-500/20"
                  : "text-gray-400 hover:text-gray-200 hover:bg-gray-800/60"
              }`}
            >
              <Icon className={`w-4 h-4 ${isActive ? "text-blue-400" : ""}`} />
              {label}
            </Link>
          );
        })}
      </nav>

      {/* Footer */}
      <div className="px-6 py-4 border-t border-gray-800/60">
        <p className="text-xs text-gray-600">Powered by</p>
        <p className="text-xs font-semibold text-gray-400 mt-0.5">
          Gemini 1.5 Flash ✦ Paytm API
        </p>
      </div>
    </aside>
  );
}
