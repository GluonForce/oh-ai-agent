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
import { api } from "@/lib/api";
import type { AuditEntry, AuditEventType } from "@/lib/types";
import { toast } from "sonner";

function eventBadge(event: AuditEventType) {
  const colors: Record<string, string> = {
    workflow_requested: "bg-blue-100 text-blue-800 border-blue-300",
    workflow_generated: "bg-green-100 text-green-800 border-green-300",
    benchmark_requested: "bg-blue-100 text-blue-800 border-blue-300",
    benchmark_generated: "bg-green-100 text-green-800 border-green-300",
    gap_analysis_requested: "bg-blue-100 text-blue-800 border-blue-300",
    gap_analysis_generated: "bg-green-100 text-green-800 border-green-300",
    knowledge_retrieved: "bg-purple-100 text-purple-800 border-purple-300",
    document_ingested: "bg-purple-100 text-purple-800 border-purple-300",
    guardrail_triggered: "bg-amber-100 text-amber-800 border-amber-300",
    error: "bg-red-100 text-red-800 border-red-300",
  };
  return (
    <Badge variant="outline" className={colors[event] ?? ""}>
      {event.replace(/_/g, " ")}
    </Badge>
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
      <div className="flex items-center justify-between flex-wrap gap-2">
        <div>
          <h1 className="text-2xl font-bold flex items-center gap-2">
            <ScrollText className="h-6 w-6" />
            Audit Trail
          </h1>
          <p className="text-muted-foreground mt-1">
            Immutable log of all agent actions for regulatory traceability.
          </p>
        </div>
        <div className="flex items-center gap-3">
          <Badge variant="secondary" className="text-sm">
            {total} total entries
          </Badge>
          <Button size="sm" variant="outline" onClick={load}>
            <RefreshCw className="mr-1 h-3 w-3" />
            Refresh
          </Button>
        </div>
      </div>

      <Card>
        <CardContent className="p-0">
          {entries.length === 0 ? (
            <div className="p-8 text-center text-muted-foreground">
              No audit entries yet. Generate a workflow or perform an action to
              create entries.
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Timestamp</TableHead>
                  <TableHead>Event</TableHead>
                  <TableHead className="hidden md:table-cell">
                    Request ID
                  </TableHead>
                  <TableHead>Actor</TableHead>
                  <TableHead className="hidden lg:table-cell">
                    Detail
                  </TableHead>
                  <TableHead className="hidden md:table-cell">
                    Model
                  </TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {entries.map((entry) => (
                  <TableRow key={entry.id}>
                    <TableCell className="text-xs text-muted-foreground whitespace-nowrap">
                      {new Date(entry.timestamp).toLocaleString()}
                    </TableCell>
                    <TableCell>{eventBadge(entry.event_type)}</TableCell>
                    <TableCell className="hidden md:table-cell text-xs font-mono text-muted-foreground">
                      {entry.request_id
                        ? entry.request_id.slice(0, 8) + "…"
                        : "—"}
                    </TableCell>
                    <TableCell className="text-sm">{entry.actor}</TableCell>
                    <TableCell className="hidden lg:table-cell text-xs text-muted-foreground max-w-64 truncate">
                      {JSON.stringify(entry.detail)}
                    </TableCell>
                    <TableCell className="hidden md:table-cell text-xs">
                      {entry.model_used ?? "—"}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
