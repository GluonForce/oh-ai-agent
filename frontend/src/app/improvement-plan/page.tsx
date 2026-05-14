"use client";

import { useState } from "react";
import { AlertTriangle, ArrowUpCircle } from "lucide-react";
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
  ImprovementPlanResponse,
  OrganisationProfile,
} from "@/lib/types";
import { toast } from "sonner";

function priorityBadge(priority: string) {
  const lower = priority.toLowerCase();
  if (lower === "high" || lower === "critical" || lower === "urgent") {
    return <Badge variant="outline" className="bg-red-100 text-red-800 border-red-300">{priority}</Badge>;
  }
  if (lower === "medium" || lower === "moderate") {
    return <Badge variant="outline" className="bg-amber-100 text-amber-800 border-amber-300">{priority}</Badge>;
  }
  if (lower === "low") {
    return <Badge variant="outline" className="bg-green-100 text-green-800 border-green-300">{priority}</Badge>;
  }
  return <Badge variant="outline">{priority}</Badge>;
}

export default function ImprovementPlanPage() {
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<ImprovementPlanResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [surveillanceFindings, setSurveillanceFindings] = useState("");

  const handleSubmit = async (
    org: OrganisationProfile,
    hazards: HazardProfile[]
  ) => {
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
      toast.error("Improvement plan generation failed");
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
          Generate an improvement plan based on surveillance findings as part of
          the PDCA ACT phase.
        </p>
      </div>

      <OrgHazardForm
        submitLabel="Generate Improvement Plan"
        loading={loading}
        onSubmit={handleSubmit}
      />

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Surveillance Findings</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-2">
            <Label htmlFor="surveillance-findings">
              Provide surveillance findings to inform the improvement plan
            </Label>
            <Textarea
              id="surveillance-findings"
              value={surveillanceFindings}
              onChange={(e) => setSurveillanceFindings(e.target.value)}
              placeholder="Summarise surveillance findings, audit results, and areas needing improvement..."
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

          {result.actions.length > 0 ? (
            <Card>
              <CardContent className="p-0">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Action Type</TableHead>
                      <TableHead>Description</TableHead>
                      <TableHead>Priority</TableHead>
                      <TableHead className="hidden lg:table-cell">
                        Regulatory Basis
                      </TableHead>
                      <TableHead className="hidden md:table-cell">
                        Expected Outcome
                      </TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {result.actions.map((action, i) => (
                      <TableRow key={i}>
                        <TableCell className="font-medium text-sm">
                          {action.action_type}
                        </TableCell>
                        <TableCell className="text-sm">
                          {action.description}
                        </TableCell>
                        <TableCell>{priorityBadge(action.priority)}</TableCell>
                        <TableCell className="hidden lg:table-cell text-sm text-muted-foreground">
                          {action.regulatory_basis}
                        </TableCell>
                        <TableCell className="hidden md:table-cell text-sm">
                          {action.expected_outcome}
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </CardContent>
            </Card>
          ) : (
            <p className="text-sm text-muted-foreground">No actions identified.</p>
          )}

          {result.management_review_items.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle className="text-base">Management Review Items</CardTitle>
              </CardHeader>
              <CardContent>
                <ul className="space-y-1">
                  {result.management_review_items.map((item, i) => (
                    <li key={i} className="text-sm text-muted-foreground">
                      • {item}
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
