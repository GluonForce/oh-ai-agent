"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Menu, Shield } from "lucide-react";
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
  SheetTrigger,
} from "@/components/ui/sheet";
import { NAV_ITEMS } from "@/lib/nav-items";
import { cn } from "@/lib/utils";

export function MobileNav() {
  const pathname = usePathname();

  return (
    <header className="flex h-14 items-center gap-3 border-b px-4 md:hidden">
      <Sheet>
        <SheetTrigger className="inline-flex h-9 w-9 cursor-pointer items-center justify-center rounded-md border border-transparent hover:bg-accent hover:text-accent-foreground focus-visible:border-ring focus-visible:ring-3 focus-visible:ring-ring/50">
          <Menu className="h-5 w-5" />
          <span className="sr-only">Open navigation</span>
        </SheetTrigger>
        <SheetContent side="left" className="w-64 p-0">
          <SheetHeader className="flex h-14 flex-row items-center gap-2 border-b px-4">
            <Shield className="h-5 w-5 text-primary" aria-hidden />
            <SheetTitle className="font-heading text-sm">OH AI Agent</SheetTitle>
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
                  <item.icon className="h-4 w-4 shrink-0" />
                  <span className="min-w-0 truncate">{item.label}</span>
                  {item.phase && (
                    <span
                      className={cn(
                        "ml-auto shrink-0 font-mono text-[0.6rem] uppercase tracking-wider",
                        active
                          ? "text-primary-foreground/70"
                          : "text-muted-foreground"
                      )}
                    >
                      {item.phase}
                    </span>
                  )}
                </Link>
              );
            })}
          </nav>
        </SheetContent>
      </Sheet>
      <Shield className="h-5 w-5 text-primary" aria-hidden />
      <span className="font-heading text-sm font-semibold tracking-tight">
        OH AI Agent
      </span>
    </header>
  );
}
