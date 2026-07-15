"use client";

import { useEffect, useState } from "react";
import {
  Activity,
  AlertTriangle,
  BookOpen,
  CheckCircle2,
  Database,
  ScrollText,
  Shield,
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Callout } from "@/components/callout";
import { PageHeader } from "@/components/page-header";
import { api, API_BASE } from "@/lib/api";
import { statusIconClass } from "@/lib/status-styles";
import type { HealthResponse, InfoResponse } from "@/lib/types";
import { cn } from "@/lib/utils";

export default function DashboardPage() {
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [info, setInfo] = useState<InfoResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    Promise.all([api.health(), api.info()])
      .then(([h, i]) => {
        setHealth(h);
        setInfo(i);
      })
      .catch((e) => setError(e.message));
  }, []);

  if (error) {
    return (
      <div className="space-y-6">
        <PageHeader title="Dashboard" />
        <Alert variant="destructive">
          <AlertTriangle className="h-4 w-4" />
          <AlertDescription>
            Failed to connect to API: {error}. Backend URL:{" "}
            <code className="font-mono text-xs">{API_BASE}</code>. Open that URL
            with <code className="font-mono text-xs">/health</code> in a new tab to
            test Railway directly, then redeploy both Railway and Vercel.
          </AlertDescription>
        </Alert>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="Dashboard"
        description="System overview and status"
      />

      {/* Asymmetric Stat-Led: dominant status + secondary metrics */}
      <div className="grid grid-cols-1 gap-4 lg:grid-cols-3">
        <Card className="lg:col-span-1 lg:row-span-1">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              System status
            </CardTitle>
            <Activity className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            {health ? (
              <div className="flex items-center gap-3">
                <CheckCircle2
                  className={cn("h-7 w-7", statusIconClass("success"))}
                />
                <span className="font-heading text-3xl font-semibold capitalize tracking-tight tabular-nums">
                  {health.status}
                </span>
              </div>
            ) : (
              <div className="h-10 w-32 animate-pulse rounded-md bg-muted" />
            )}
            {health && (
              <div className="mt-4 flex items-center gap-2">
                <Shield className="h-3.5 w-3.5 text-muted-foreground" />
                <Badge variant="secondary" className="font-mono text-xs">
                  {health.environment}
                </Badge>
              </div>
            )}
          </CardContent>
        </Card>

        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:col-span-2">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground">
                Knowledge chunks
              </CardTitle>
              <Database className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              {health ? (
                <span className="font-heading text-2xl font-semibold tabular-nums tracking-tight">
                  {health.knowledge_chunks}
                </span>
              ) : (
                <div className="h-8 w-16 animate-pulse rounded-md bg-muted" />
              )}
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground">
                Audit entries
              </CardTitle>
              <ScrollText className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              {health ? (
                <span className="font-heading text-2xl font-semibold tabular-nums tracking-tight">
                  {health.audit_entries}
                </span>
              ) : (
                <div className="h-8 w-16 animate-pulse rounded-md bg-muted" />
              )}
            </CardContent>
          </Card>
        </div>
      </div>

      {info && (
        <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-base">
                <BookOpen className="h-4 w-4 text-primary" />
                System information
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <div className="flex justify-between text-sm">
                <span className="text-muted-foreground">Application</span>
                <span className="font-medium">{info.name}</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-muted-foreground">Version</span>
                <span className="font-mono text-sm font-medium">{info.version}</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-muted-foreground">LLM Model</span>
                <Badge variant="outline" className="font-mono text-xs">
                  {info.llm_model}
                </Badge>
              </div>
              {info.framework && (
                <div className="flex justify-between text-sm">
                  <span className="text-muted-foreground">Framework</span>
                  <Badge variant="outline">{info.framework}</Badge>
                </div>
              )}
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-base">
                <AlertTriangle className="h-4 w-4 text-warning" />
                Mandatory disclaimers
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-2">
              {info.disclaimers.map((d, i) => (
                <Callout key={i} tone="warning">
                  <p className="text-sm leading-relaxed text-muted-foreground">{d}</p>
                </Callout>
              ))}
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
}
