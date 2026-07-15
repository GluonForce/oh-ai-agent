import {
  ArrowUpCircle,
  BookOpen,
  ClipboardCheck,
  LayoutDashboard,
  ScrollText,
  ShieldCheck,
  TrendingUp,
  type LucideIcon,
} from "lucide-react";

export type NavItem = {
  href: string;
  label: string;
  icon: LucideIcon;
  phase?: string;
};

export const NAV_ITEMS: NavItem[] = [
  { href: "/", label: "Dashboard", icon: LayoutDashboard },
  {
    href: "/workflows",
    label: "Workflow Generator",
    icon: ClipboardCheck,
    phase: "PLAN + DO",
  },
  {
    href: "/compliance-audit",
    label: "Compliance Audit",
    icon: ShieldCheck,
    phase: "CHECK",
  },
  {
    href: "/trend-analysis",
    label: "Trend Analysis",
    icon: TrendingUp,
    phase: "REVIEW",
  },
  {
    href: "/improvement-plan",
    label: "Improvement Plan",
    icon: ArrowUpCircle,
    phase: "ACT",
  },
  { href: "/knowledge", label: "Knowledge Base", icon: BookOpen },
  { href: "/audit", label: "Audit Trail", icon: ScrollText },
];
