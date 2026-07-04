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
import { api, API_BASE } from "@/lib/api";
import type { HealthResponse, InfoResponse } from "@/lib/types";

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
        <h1 className="text-2xl font-bold">Dashboard</h1>
        <Alert variant="destructive">
          <AlertTriangle className="h-4 w-4" />
          <AlertDescription>
            Failed to connect to API: {error}. Backend URL:{" "}
            <code className="text-xs">{API_BASE}</code>. Open that URL
            with <code className="text-xs">/health</code> in a new tab to test
            Railway directly, then redeploy both Railway and Vercel.
          </AlertDescription>
        </Alert>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Dashboard</h1>
        <p className="text-muted-foreground mt-1">
          System overview and status
        </p>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Status
            </CardTitle>
            <Activity className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            {health ? (
              <div className="flex items-center gap-2">
                <CheckCircle2 className="h-5 w-5 text-green-500" />
                <span className="text-2xl font-bold capitalize">
                  {health.status}
                </span>
              </div>
            ) : (
              <div className="h-8 w-24 bg-muted animate-pulse rounded" />
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Environment
            </CardTitle>
            <Shield className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            {health ? (
              <Badge variant="secondary" className="text-base px-3 py-1">
                {health.environment}
              </Badge>
            ) : (
              <div className="h-8 w-28 bg-muted animate-pulse rounded" />
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Knowledge Chunks
            </CardTitle>
            <Database className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            {health ? (
              <span className="text-2xl font-bold">
                {health.knowledge_chunks}
              </span>
            ) : (
              <div className="h-8 w-16 bg-muted animate-pulse rounded" />
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Audit Entries
            </CardTitle>
            <ScrollText className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            {health ? (
              <span className="text-2xl font-bold">
                {health.audit_entries}
              </span>
            ) : (
              <div className="h-8 w-16 bg-muted animate-pulse rounded" />
            )}
          </CardContent>
        </Card>
      </div>

      {info && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          <Card>
            <CardHeader>
              <CardTitle className="text-base flex items-center gap-2">
                <BookOpen className="h-4 w-4" />
                System Information
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <div className="flex justify-between text-sm">
                <span className="text-muted-foreground">Application</span>
                <span className="font-medium">{info.name}</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-muted-foreground">Version</span>
                <span className="font-medium">{info.version}</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-muted-foreground">LLM Model</span>
                <Badge variant="outline">{info.llm_model}</Badge>
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
              <CardTitle className="text-base flex items-center gap-2">
                <AlertTriangle className="h-4 w-4" />
                Mandatory Disclaimers
              </CardTitle>
            </CardHeader>
            <CardContent>
              <ul className="space-y-2">
                {info.disclaimers.map((d, i) => (
                  <li
                    key={i}
                    className="text-sm text-muted-foreground leading-relaxed border-l-2 border-amber-500 pl-3"
                  >
                    {d}
                  </li>
                ))}
              </ul>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
}
