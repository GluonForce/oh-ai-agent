import { cn } from "@/lib/utils";

/** Semantic status surfaces — always from design tokens, never raw Tailwind palette. */
export const statusToneClass = {
  success:
    "border-success/30 bg-success-muted text-success-foreground",
  warning:
    "border-warning/30 bg-warning-muted text-warning-foreground",
  danger: "border-danger/30 bg-danger-muted text-danger-foreground",
  info: "border-info/30 bg-info-muted text-info-foreground",
  neutral:
    "border-neutral-status/30 bg-neutral-status-muted text-neutral-status-foreground",
} as const;

export type StatusTone = keyof typeof statusToneClass;

export function complianceTone(
  rating: string
): StatusTone {
  switch (rating) {
    case "compliant":
      return "success";
    case "partially_compliant":
      return "warning";
    case "non_compliant":
      return "danger";
    default:
      return "neutral";
  }
}

export function priorityTone(priority: string): StatusTone {
  switch (priority) {
    case "high":
      return "danger";
    case "medium":
      return "warning";
    default:
      return "success";
  }
}

export function auditEventTone(event: string): StatusTone {
  if (event.includes("error")) return "danger";
  if (event.includes("guardrail")) return "warning";
  if (event.includes("knowledge") || event.includes("document")) return "info";
  if (event.includes("generated")) return "success";
  if (event.includes("requested")) return "info";
  return "neutral";
}

export function statusIconClass(tone: StatusTone): string {
  return cn({
    "text-success": tone === "success",
    "text-warning": tone === "warning",
    "text-danger": tone === "danger",
    "text-info": tone === "info",
    "text-neutral-status": tone === "neutral",
  });
}
