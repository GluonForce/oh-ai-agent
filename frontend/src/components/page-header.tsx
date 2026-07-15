import type { LucideIcon } from "lucide-react";
import type { ReactNode } from "react";
import { cn } from "@/lib/utils";

export function PageHeader({
  title,
  description,
  icon: Icon,
  phase,
  actions,
  className,
}: {
  title: string;
  description?: string;
  icon?: LucideIcon;
  phase?: string;
  actions?: ReactNode;
  className?: string;
}) {
  return (
    <div
      className={cn(
        "flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between",
        className
      )}
    >
      <div className="min-w-0 space-y-1.5">
        {phase && (
          <p className="font-mono text-[0.65rem] font-medium uppercase tracking-[0.08em] text-primary">
            {phase}
          </p>
        )}
        <h1 className="font-heading text-2xl font-semibold tracking-tight text-foreground">
          <span className="inline-flex items-center gap-2">
            {Icon && (
              <Icon className="h-5 w-5 shrink-0 text-primary" aria-hidden />
            )}
            {title}
          </span>
        </h1>
        {description && (
          <p className="max-w-2xl text-sm leading-relaxed text-muted-foreground">
            {description}
          </p>
        )}
      </div>
      {actions && (
        <div className="flex shrink-0 flex-wrap items-center gap-2">{actions}</div>
      )}
    </div>
  );
}
