"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  Activity,
  BookOpen,
  ClipboardCheck,
  FileSearch,
  LayoutDashboard,
  ScrollText,
  Shield,
} from "lucide-react";
import { cn } from "@/lib/utils";

const NAV_ITEMS = [
  { href: "/", label: "Dashboard", icon: LayoutDashboard },
  { href: "/workflows", label: "PDCA Workflow", icon: ClipboardCheck },
  { href: "/benchmark", label: "Benchmarking", icon: Activity },
  { href: "/gap-analysis", label: "Gap Analysis", icon: FileSearch },
  { href: "/knowledge", label: "Knowledge Base", icon: BookOpen },
  { href: "/audit", label: "Audit Trail", icon: ScrollText },
];

export function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="hidden md:flex md:w-64 md:flex-col border-r bg-muted/30">
      <div className="flex h-14 items-center border-b px-4">
        <Shield className="mr-2 h-5 w-5 text-primary" />
        <span className="font-semibold text-sm">OH AI Agent</span>
      </div>
      <nav className="flex-1 space-y-1 p-3">
        {NAV_ITEMS.map((item) => {
          const active =
            item.href === "/"
              ? pathname === "/"
              : pathname.startsWith(item.href);
          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                "flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium transition-colors",
                active
                  ? "bg-primary text-primary-foreground"
                  : "text-muted-foreground hover:bg-muted hover:text-foreground"
              )}
            >
              <item.icon className="h-4 w-4" />
              {item.label}
            </Link>
          );
        })}
      </nav>
      <div className="border-t p-4">
        <p className="text-xs text-muted-foreground leading-relaxed">
          PDCA-aligned occupational health workflows for the UK.
        </p>
      </div>
    </aside>
  );
}
