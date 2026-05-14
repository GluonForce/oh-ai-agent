"use client";

import { useState } from "react";
import { AlertTriangle, TrendingUp } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Separator } from "@/components/ui/separator";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
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

function severityBadge(severity: string) {
  const lower = severity.toLowerCase();
  if (lower === "high" || lower === "critical") {
    return <Badge variant="outline" className="bg-red-100 text-red-800 border-red-300">{severity}</Badge>;
  }
  if (lower === "medium" || lower === "moderate") {
    return <Badge variant="outline" className="bg-amber-100 text-amber-800 border-amber-300">{severity}</Badge>;
  }
  if (lower === "low") {
    return <Badge variant="outline" className="bg-green-100 text-green-800 border-green-300">{severity}</Badge>;
  }
  return <Badge variant="outline">{severity}</Badge>;
}

export default function TrendAnalysisPage() {
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<TrendAnalysisResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [surveillanceSummary, setSurveillanceSummary] = useState("");

  const handleSubmit = async (
    org: OrganisationProfile,
    hazards: HazardProfile[]
  ) => {
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
      toast.error("Trend analysis failed");
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
          Review surveillance trends and control effectiveness as part of the
          PDCA REVIEW phase.
        </p>
      </div>

      <OrgHazardForm
        submitLabel="Run Trend Analysis"
        loading={loading}
        onSubmit={handleSubmit}
      />

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Surveillance Summary</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-2">
            <Label htmlFor="surveillance-summary">
              Provide a summary of surveillance data and findings
            </Label>
            <Textarea
              id="surveillance-summary"
              value={surveillanceSummary}
              onChange={(e) => setSurveillanceSummary(e.target.value)}
              placeholder="Summarise your surveillance data, trends observed, and any concerns..."
              rows={4}
            />
          </div>
        </CardContent>
      </Card>

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
          <h2 className="text-lg font-semibold">
            Results for {result.organisation_name}
          </h2>

          {result.findings.length > 0 ? (
            <Card>
              <CardContent className="p-0">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Category</TableHead>
                      <TableHead>Description</TableHead>
                      <TableHead>Affected Area</TableHead>
                      <TableHead>Severity</TableHead>
                      <TableHead className="hidden lg:table-cell">
                        Recommended Action
                      </TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {result.findings.map((finding, i) => (
                      <TableRow key={i}>
                        <TableCell className="font-medium text-sm">
                          {finding.category}
                        </TableCell>
                        <TableCell className="text-sm">
                          {finding.description}
                        </TableCell>
                        <TableCell className="text-sm">
                          {finding.affected_area}
                        </TableCell>
                        <TableCell>{severityBadge(finding.severity)}</TableCell>
                        <TableCell className="hidden lg:table-cell text-sm">
                          {finding.recommended_action}
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </CardContent>
            </Card>
          ) : (
            <p className="text-sm text-muted-foreground">No findings identified.</p>
          )}

          {result.control_effectiveness_indicators.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle className="text-base">Control Effectiveness Indicators</CardTitle>
              </CardHeader>
              <CardContent>
                <ul className="space-y-1">
                  {result.control_effectiveness_indicators.map((indicator, i) => (
                    <li key={i} className="text-sm text-muted-foreground">
                      • {indicator}
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
