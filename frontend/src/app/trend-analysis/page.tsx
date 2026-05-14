"use client";

import { useState } from "react";
import { AlertTriangle, TrendingUp } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Separator } from "@/components/ui/separator";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { OrgHazardForm } from "@/components/org-hazard-form";
import { api } from "@/lib/api";
import type {
  HazardProfile,
  OrganisationProfile,
  TrendAnalysisResponse,
} from "@/lib/types";
import { toast } from "sonner";

export default function TrendAnalysisPage() {
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<TrendAnalysisResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [surveillanceSummary, setSurveillanceSummary] = useState("");

  const handleSubmit = async (
    org: OrganisationProfile,
    hazards: HazardProfile[]
  ) => {
    if (!surveillanceSummary.trim()) {
      toast.error("Surveillance summary is required");
      return;
    }
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const res = await api.trendAnalysis({
        organisation: org,
        hazards,
        surveillance_summary: surveillanceSummary,
      });
      setResult(res);
      toast.success("Trend analysis completed");
    } catch (e) {
      const msg = e instanceof Error ? e.message : "Unknown error";
      setError(msg);
      toast.error("Failed to run trend analysis");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6 max-w-5xl">
      <div>
        <h1 className="text-2xl font-bold flex items-center gap-2">
          <TrendingUp className="h-6 w-6" />
          Trend Analysis
          <Badge variant="secondary" className="text-xs">REVIEW</Badge>
        </h1>
        <p className="text-muted-foreground mt-1">
          Analyse anonymised surveillance data to identify trends, evaluate
          control effectiveness, and highlight emerging risks across your
          occupational health programme.
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Surveillance Summary *</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-2">
            <Label htmlFor="surveillance-summary">
              Provide a summary of your surveillance data for analysis
            </Label>
            <Textarea
              id="surveillance-summary"
              value={surveillanceSummary}
              onChange={(e) => setSurveillanceSummary(e.target.value)}
              placeholder="e.g. Over the last 12 months, 15 audiometry tests were conducted with 3 showing threshold shifts. Spirometry results for paint shop workers show a declining trend in FEV1..."
              rows={4}
              required
            />
          </div>
        </CardContent>
      </Card>

      <OrgHazardForm
        submitLabel="Run Trend Analysis"
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
          <div className="flex items-center justify-between flex-wrap gap-2">
            <h2 className="text-lg font-semibold">
              Trend Analysis — {result.organisation_name}
            </h2>
            <Badge variant="outline">{result.model_used}</Badge>
          </div>

          {result.findings.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle className="text-base flex items-center gap-2">
                  <TrendingUp className="h-4 w-4" />
                  Findings ({result.findings.length})
                </CardTitle>
              </CardHeader>
              <CardContent className="p-0">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Area</TableHead>
                      <TableHead>Observation</TableHead>
                      <TableHead className="hidden lg:table-cell">Implication</TableHead>
                      <TableHead className="hidden md:table-cell">Recommended Action</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {result.findings.map((f, i) => (
                      <TableRow key={i}>
                        <TableCell className="font-medium text-sm">{f.area}</TableCell>
                        <TableCell className="text-sm">{f.observation}</TableCell>
                        <TableCell className="hidden lg:table-cell text-sm">{f.implication}</TableCell>
                        <TableCell className="hidden md:table-cell text-sm">{f.recommended_action || "—"}</TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </CardContent>
            </Card>
          )}

          {result.control_effectiveness_indicators.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle className="text-base">Control Effectiveness Indicators</CardTitle>
              </CardHeader>
              <CardContent>
                <ul className="space-y-2">
                  {result.control_effectiveness_indicators.map((ind, i) => (
                    <li key={i} className="text-sm text-muted-foreground border-l-2 border-blue-500 pl-3">
                      {ind}
                    </li>
                  ))}
                </ul>
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
                    <Badge key={i} variant="secondary">{s}</Badge>
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
