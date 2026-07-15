"use client";

import { useEffect, useState } from "react";
import { RefreshCw, ScrollText } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { PageHeader } from "@/components/page-header";
import { StatusBadge } from "@/components/status-badge";
import { api } from "@/lib/api";
import { auditEventTone } from "@/lib/status-styles";
import type { AuditEntry, AuditEventType } from "@/lib/types";
import { toast } from "sonner";

function eventBadge(event: AuditEventType) {
  return (
    <StatusBadge tone={auditEventTone(event)}>
      {event.replace(/_/g, " ")}
    </StatusBadge>
  );
}

export default function AuditPage() {
  const [entries, setEntries] = useState<AuditEntry[]>([]);
  const [total, setTotal] = useState(0);

  const load = () => {
    Promise.all([api.auditTrail(200), api.auditCount()])
      .then(([e, c]) => {
        setEntries(e.reverse());
        setTotal(c.total_entries);
      })
      .catch(() => toast.error("Failed to load audit trail"));
  };

  useEffect(load, []);

  return (
    <div className="space-y-6">
      <PageHeader
        title="Audit Trail"
        icon={ScrollText}
        description="Immutable log of all agent actions for regulatory traceability."
        actions={
          <>
            <Badge variant="secondary" className="font-mono text-sm tabular-nums">
              {total} total entries
            </Badge>
            <Button size="sm" variant="outline" onClick={load}>
              <RefreshCw className="mr-1 h-3 w-3" />
              Refresh
            </Button>
          </>
        }
      />

      <Card>
        <CardContent className="p-0">
          {entries.length === 0 ? (
            <div className="p-8 text-center text-muted-foreground">
              No audit entries yet. Generate a workflow or perform an action to
              create entries.
            </div>
          ) : (
            <TooltipProvider>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Timestamp</TableHead>
                    <TableHead>Event</TableHead>
                    <TableHead className="hidden md:table-cell">
                      Request ID
                    </TableHead>
                    <TableHead>Actor</TableHead>
                    <TableHead className="hidden lg:table-cell">Detail</TableHead>
                    <TableHead className="hidden md:table-cell">Model</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {entries.map((entry) => (
                    <TableRow key={entry.id}>
                      <TableCell className="whitespace-nowrap font-mono text-xs text-muted-foreground tabular-nums">
                        {new Date(entry.timestamp).toLocaleString()}
                      </TableCell>
                      <TableCell>{eventBadge(entry.event_type)}</TableCell>
                      <TableCell className="hidden font-mono text-xs text-muted-foreground md:table-cell">
                        {entry.request_id ? (
                          <Tooltip>
                            <TooltipTrigger className="cursor-default underline decoration-dotted underline-offset-2">
                              {entry.request_id.slice(0, 8)}…
                            </TooltipTrigger>
                            <TooltipContent>
                              <span className="font-mono text-xs">
                                {entry.request_id}
                              </span>
                            </TooltipContent>
                          </Tooltip>
                        ) : (
                          "—"
                        )}
                      </TableCell>
                      <TableCell className="text-sm">{entry.actor}</TableCell>
                      <TableCell className="hidden max-w-64 truncate text-xs text-muted-foreground lg:table-cell">
                        {JSON.stringify(entry.detail)}
                      </TableCell>
                      <TableCell className="hidden font-mono text-xs md:table-cell">
                        {entry.model_used ?? "—"}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TooltipProvider>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
