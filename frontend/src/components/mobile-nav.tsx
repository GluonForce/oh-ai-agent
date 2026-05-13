"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Menu, Shield } from "lucide-react";
import {
  Activity,
  BookOpen,
  ClipboardCheck,
  FileSearch,
  LayoutDashboard,
  ScrollText,
} from "lucide-react";
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
  SheetTrigger,
} from "@/components/ui/sheet";
import { cn } from "@/lib/utils";

const NAV_ITEMS = [
  { href: "/", label: "Dashboard", icon: LayoutDashboard },
  { href: "/workflows", label: "Workflow Generator", icon: ClipboardCheck },
  { href: "/benchmark", label: "Benchmarking", icon: Activity },
  { href: "/gap-analysis", label: "Gap Analysis", icon: FileSearch },
  { href: "/knowledge", label: "Knowledge Base", icon: BookOpen },
  { href: "/audit", label: "Audit Trail", icon: ScrollText },
];

export function MobileNav() {
  const pathname = usePathname();

  return (
    <header className="flex md:hidden h-14 items-center border-b px-4 gap-3">
      <Sheet>
        <SheetTrigger className="inline-flex items-center justify-center rounded-md h-9 w-9 hover:bg-accent hover:text-accent-foreground cursor-pointer">
          <Menu className="h-5 w-5" />
        </SheetTrigger>
        <SheetContent side="left" className="w-64 p-0">
          <SheetHeader className="h-14 flex-row items-center border-b px-4 gap-2">
            <Shield className="h-5 w-5 text-primary" />
            <SheetTitle className="text-sm">OH AI Agent</SheetTitle>
          </SheetHeader>
          <nav className="space-y-1 p-3">
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
        </SheetContent>
      </Sheet>
      <Shield className="h-5 w-5 text-primary" />
      <span className="font-semibold text-sm">OH AI Agent</span>
    </header>
  );
}
