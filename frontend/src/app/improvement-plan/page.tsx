"use client";

import { useState } from "react";
import { AlertTriangle, ArrowUpCircle } from "lucide-react";
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
  ImprovementPlanResponse,
} from "@/lib/types";
import { toast } from "sonner";

export default function ImprovementPlanPage() {
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<ImprovementPlanResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [surveillanceFindings, setSurveillanceFindings] = useState("");

  const handleSubmit = async (
    org: OrganisationProfile,
    hazards: HazardProfile[]
  ) => {
    if (!surveillanceFindings.trim()) {
      toast.error("Surveillance findings are required");
      return;
    }
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const res = await api.improvementPlan({
        organisation: org,
        hazards,
        surveillance_findings: surveillanceFindings,
      });
      setResult(res);
      toast.success("Improvement plan generated");
    } catch (e) {
      const msg = e instanceof Error ? e.message : "Unknown error";
      setError(msg);
      toast.error("Failed to generate improvement plan");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6 max-w-5xl">
      <div>
        <h1 className="text-2xl font-bold flex items-center gap-2">
          <ArrowUpCircle className="h-6 w-6" />
          Improvement Plan
          <Badge variant="secondary" className="text-xs">ACT</Badge>
        </h1>
        <p className="text-muted-foreground mt-1">
          Generate prioritised improvement actions based on surveillance
          findings and regulatory requirements. This ACT-phase tool helps close
          the PDCA loop with concrete, auditable recommendations.
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Surveillance Findings *</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-2">
            <Label htmlFor="surveillance-findings">
              Describe the findings from your surveillance programme
            </Label>
            <Textarea
              id="surveillance-findings"
              value={surveillanceFindings}
              onChange={(e) => setSurveillanceFindings(e.target.value)}
              placeholder="e.g. Audiometry results show 3 out of 15 workers have threshold shifts above action level. Two workers in the paint shop show declining FEV1 trends..."
              rows={4}
              required
            />
          </div>
        </CardContent>
      </Card>

      <OrgHazardForm
        submitLabel="Generate Improvement Plan"
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
              Improvement Plan — {result.organisation_name}
            </h2>
            <Badge variant="outline">{result.model_used}</Badge>
          </div>

          {result.actions.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle className="text-base flex items-center gap-2">
                  <ArrowUpCircle className="h-4 w-4" />
                  Actions ({result.actions.length})
                </CardTitle>
              </CardHeader>
              <CardContent className="p-0">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Area</TableHead>
                      <TableHead>Action</TableHead>
                      <TableHead className="hidden lg:table-cell">Rationale</TableHead>
                      <TableHead>Priority</TableHead>
                      <TableHead className="hidden md:table-cell">Regulatory Reference</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {result.actions.map((a, i) => (
                      <TableRow key={i}>
                        <TableCell className="font-medium text-sm">{a.area}</TableCell>
                        <TableCell className="text-sm">{a.action}</TableCell>
                        <TableCell className="hidden lg:table-cell text-sm">{a.rationale}</TableCell>
                        <TableCell>
                          <Badge
                            variant="outline"
                            className={
                              a.priority === "high"
                                ? "bg-red-100 text-red-800 border-red-300"
                                : a.priority === "medium"
                                  ? "bg-amber-100 text-amber-800 border-amber-300"
                                  : "bg-green-100 text-green-800 border-green-300"
                            }
                          >
                            {a.priority}
                          </Badge>
                        </TableCell>
                        <TableCell className="hidden md:table-cell text-sm text-muted-foreground">
                          {a.regulatory_reference || "—"}
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </CardContent>
            </Card>
          )}

          {result.management_review_items.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle className="text-base">Management Review Items</CardTitle>
              </CardHeader>
              <CardContent>
                <ul className="space-y-2">
                  {result.management_review_items.map((item, i) => (
                    <li key={i} className="text-sm text-muted-foreground border-l-2 border-amber-500 pl-3">
                      {item}
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
