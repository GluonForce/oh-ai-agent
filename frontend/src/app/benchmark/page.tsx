"use client";

import { useState } from "react";
import { Activity, AlertTriangle, CheckCircle2, XCircle } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Separator } from "@/components/ui/separator";
import { OrgHazardForm } from "@/components/org-hazard-form";
import { api } from "@/lib/api";
import type {
  BenchmarkResult,
  HazardProfile,
  OrganisationProfile,
} from "@/lib/types";
import { toast } from "sonner";

export default function BenchmarkPage() {
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<BenchmarkResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (
    org: OrganisationProfile,
    hazards: HazardProfile[]
  ) => {
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const res = await api.benchmark({ organisation: org, hazards });
      setResult(res);
      toast.success("Benchmark completed");
    } catch (e) {
      const msg = e instanceof Error ? e.message : "Unknown error";
      setError(msg);
      toast.error("Benchmark failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6 max-w-4xl">
      <div>
        <h1 className="text-2xl font-bold flex items-center gap-2">
          <Activity className="h-6 w-6" />
          Benchmarking
        </h1>
        <p className="text-muted-foreground mt-1">
          Benchmark your organisation&apos;s current OH practice against UK
          regulatory minimum requirements.
        </p>
      </div>

      <OrgHazardForm
        submitLabel="Run Benchmark"
        loading={loading}
        onSubmit={handleSubmit}
      />

      {error && (
        <Alert variant="destructive">
          <AlertTriangle className="h-4 w-4" />
          <AlertTitle>Error</AlertTitle>
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      {result && (
        <div className="space-y-4">
          <Separator />
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm text-muted-foreground">
                  Areas Assessed
                </CardTitle>
              </CardHeader>
              <CardContent>
                <span className="text-2xl font-bold">
                  {result.areas_assessed.length}
                </span>
              </CardContent>
            </Card>
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm text-muted-foreground flex items-center gap-1">
                  <CheckCircle2 className="h-3 w-3 text-green-500" />
                  Compliant
                </CardTitle>
              </CardHeader>
              <CardContent>
                <span className="text-2xl font-bold text-green-600">
                  {result.compliant_areas.length}
                </span>
              </CardContent>
            </Card>
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm text-muted-foreground flex items-center gap-1">
                  <XCircle className="h-3 w-3 text-red-500" />
                  Non-Compliant
                </CardTitle>
              </CardHeader>
              <CardContent>
                <span className="text-2xl font-bold text-red-600">
                  {result.non_compliant_areas.length}
                </span>
              </CardContent>
            </Card>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            <Card>
              <CardHeader>
                <CardTitle className="text-base text-green-700 flex items-center gap-2">
                  <CheckCircle2 className="h-4 w-4" />
                  Compliant Areas
                </CardTitle>
              </CardHeader>
              <CardContent>
                {result.compliant_areas.length === 0 ? (
                  <p className="text-sm text-muted-foreground">None identified</p>
                ) : (
                  <ul className="space-y-1">
                    {result.compliant_areas.map((a, i) => (
                      <li key={i} className="text-sm flex items-start gap-2">
                        <CheckCircle2 className="h-3 w-3 text-green-500 mt-1 shrink-0" />
                        {a}
                      </li>
                    ))}
                  </ul>
                )}
              </CardContent>
            </Card>
            <Card>
              <CardHeader>
                <CardTitle className="text-base text-red-700 flex items-center gap-2">
                  <XCircle className="h-4 w-4" />
                  Non-Compliant Areas
                </CardTitle>
              </CardHeader>
              <CardContent>
                {result.non_compliant_areas.length === 0 ? (
                  <p className="text-sm text-muted-foreground">None identified</p>
                ) : (
                  <ul className="space-y-1">
                    {result.non_compliant_areas.map((a, i) => (
                      <li key={i} className="text-sm flex items-start gap-2">
                        <XCircle className="h-3 w-3 text-red-500 mt-1 shrink-0" />
                        {a}
                      </li>
                    ))}
                  </ul>
                )}
              </CardContent>
            </Card>
          </div>

          {result.recommendations.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle className="text-base">Recommendations</CardTitle>
              </CardHeader>
              <CardContent>
                <ol className="space-y-2 list-decimal list-inside">
                  {result.recommendations.map((r, i) => (
                    <li key={i} className="text-sm">
                      {r}
                    </li>
                  ))}
                </ol>
              </CardContent>
            </Card>
          )}

          {result.sources_cited.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle className="text-base">Sources Cited</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="flex flex-wrap gap-2">
                  {result.sources_cited.map((s, i) => (
                    <Badge key={i} variant="secondary">
                      {s}
                    </Badge>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}
        </div>
      )}
    </div>
  );
}
