"use client";

import { useState } from "react";
import { AlertTriangle, CheckCircle2, ShieldCheck, XCircle } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
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
  ComplianceAuditResponse,
  ComplianceRating,
} from "@/lib/types";
import { toast } from "sonner";

function ratingBadge(rating: ComplianceRating) {
  const variants: Record<ComplianceRating, { label: string; cls: string }> = {
    compliant: { label: "Compliant", cls: "bg-green-100 text-green-800 border-green-300" },
    partially_compliant: { label: "Partial", cls: "bg-amber-100 text-amber-800 border-amber-300" },
    non_compliant: { label: "Non-Compliant", cls: "bg-red-100 text-red-800 border-red-300" },
    not_assessed: { label: "Not Assessed", cls: "bg-gray-100 text-gray-800 border-gray-300" },
  };
  const v = variants[rating];
  return (
    <Badge variant="outline" className={v.cls}>
      {v.label}
    </Badge>
  );
}

function boolIndicator(value: boolean, label: string) {
  return (
    <div className="flex items-center gap-2 text-sm">
      {value ? (
        <CheckCircle2 className="h-4 w-4 text-green-500" />
      ) : (
        <XCircle className="h-4 w-4 text-red-500" />
      )}
      <span>{label}</span>
    </div>
  );
}

export default function ComplianceAuditPage() {
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<ComplianceAuditResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (
    org: OrganisationProfile,
    hazards: HazardProfile[]
  ) => {
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const res = await api.complianceAudit({ organisation: org, hazards });
      setResult(res);
      toast.success("Compliance audit completed");
    } catch (e) {
      const msg = e instanceof Error ? e.message : "Unknown error";
      setError(msg);
      toast.error("Failed to run compliance audit");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6 max-w-5xl">
      <div>
        <h1 className="text-2xl font-bold flex items-center gap-2">
          <ShieldCheck className="h-6 w-6" />
          Compliance Audit
          <Badge variant="secondary" className="text-xs">CHECK</Badge>
        </h1>
        <p className="text-muted-foreground mt-1">
          Evaluate statutory occupational health compliance against UK regulatory
          requirements. This CHECK-phase tool audits your current arrangements
          and identifies areas needing attention.
        </p>
      </div>

      <OrgHazardForm
        submitLabel="Run Compliance Audit"
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
            <h2 className="text-lg font-semibold">Audit Results — {result.organisation_name}</h2>
            <Badge variant="outline">{result.model_used}</Badge>
          </div>

          <div className="flex flex-wrap gap-4">
            <div className="flex items-center gap-2">
              <span className="text-sm font-medium">Overall Rating:</span>
              {ratingBadge(result.overall_rating)}
            </div>
          </div>

          <Card>
            <CardHeader>
              <CardTitle className="text-base">Assessment Indicators</CardTitle>
            </CardHeader>
            <CardContent className="flex flex-wrap gap-6">
              {boolIndicator(result.employee_coverage_assessed, "Employee Coverage Assessed")}
              {boolIndicator(result.interval_adherence_assessed, "Interval Adherence Assessed")}
              {boolIndicator(result.governance_assessed, "Governance Assessed")}
            </CardContent>
          </Card>

          {result.audit_items.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle className="text-base flex items-center gap-2">
                  <ShieldCheck className="h-4 w-4" />
                  Audit Items ({result.audit_items.length})
                </CardTitle>
              </CardHeader>
              <CardContent className="p-0">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Area</TableHead>
                      <TableHead>Question</TableHead>
                      <TableHead>Status</TableHead>
                      <TableHead className="hidden lg:table-cell">Finding</TableHead>
                      <TableHead className="hidden md:table-cell">Recommendation</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {result.audit_items.map((item, i) => (
                      <TableRow key={i}>
                        <TableCell className="font-medium text-sm">{item.area}</TableCell>
                        <TableCell className="text-sm">{item.question}</TableCell>
                        <TableCell>
                          <Badge
                            variant="outline"
                            className={
                              item.status === "compliant"
                                ? "bg-green-100 text-green-800 border-green-300"
                                : item.status === "partially_compliant"
                                  ? "bg-amber-100 text-amber-800 border-amber-300"
                                  : item.status === "non_compliant"
                                    ? "bg-red-100 text-red-800 border-red-300"
                                    : "bg-gray-100 text-gray-800 border-gray-300"
                            }
                          >
                            {item.status.replace(/_/g, " ")}
                          </Badge>
                        </TableCell>
                        <TableCell className="hidden lg:table-cell text-sm">{item.finding || "—"}</TableCell>
                        <TableCell className="hidden md:table-cell text-sm">{item.recommendation || "—"}</TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
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
