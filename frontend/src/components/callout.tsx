import type { ReactNode } from "react";
import { cn } from "@/lib/utils";
import type { StatusTone } from "@/lib/status-styles";

const tickClass: Record<StatusTone, string> = {
  success: "bg-success",
  warning: "bg-warning",
  danger: "bg-danger",
  info: "bg-info",
  neutral: "bg-neutral-status",
};

/** Hairline callout with a corner accent tick — replaces side-stripe cards. */
export function Callout({
  tone = "warning",
  children,
  className,
}: {
  tone?: StatusTone;
  children: ReactNode;
  className?: string;
}) {
  return (
    <div
      className={cn(
        "relative rounded-md border border-border bg-card px-3 py-2.5 pl-4",
        className
      )}
    >
      <span
        aria-hidden
        className={cn(
          "absolute top-2.5 left-0 h-4 w-0.5 rounded-full",
          tickClass[tone]
        )}
      />
      {children}
    </div>
  );
}
