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
  ComplianceAuditResponse,
  ComplianceRating,
  HazardProfile,
  OrganisationProfile,
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
    <div className="flex items-center gap-2">
      {value ? (
        <CheckCircle2 className="h-4 w-4 text-green-500" />
      ) : (
        <XCircle className="h-4 w-4 text-red-500" />
      )}
      <span className="text-sm">{label}</span>
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
      toast.error("Compliance audit failed");
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
          Audit your organisation&apos;s OH compliance against UK regulatory
          requirements using the PDCA CHECK phase.
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
            <h2 className="text-lg font-semibold">
              Results for {result.organisation_name}
            </h2>
            <div className="flex items-center gap-2">
              <span className="text-sm text-muted-foreground">Overall:</span>
              {ratingBadge(result.overall_rating)}
            </div>
          </div>

          <Card>
            <CardHeader>
              <CardTitle className="text-base">Assessment Indicators</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex flex-wrap gap-6">
                {boolIndicator(result.employee_coverage_assessed, "Employee Coverage Assessed")}
                {boolIndicator(result.interval_adherence_assessed, "Interval Adherence Assessed")}
                {boolIndicator(result.governance_assessed, "Governance Assessed")}
              </div>
            </CardContent>
          </Card>

          {result.audit_items.length > 0 ? (
            <Card>
              <CardContent className="p-0">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Area</TableHead>
                      <TableHead>Question</TableHead>
                      <TableHead>Current State</TableHead>
                      <TableHead>Required State</TableHead>
                      <TableHead>Rating</TableHead>
                      <TableHead className="hidden lg:table-cell">
                        Recommendation
                      </TableHead>
                      <TableHead className="hidden md:table-cell">
                        Regulation
                      </TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {result.audit_items.map((item, i) => (
                      <TableRow key={i}>
                        <TableCell className="font-medium text-sm">
                          {item.area}
                        </TableCell>
                        <TableCell className="text-sm">
                          {item.question}
                        </TableCell>
                        <TableCell className="text-sm">
                          {item.current_state}
                        </TableCell>
                        <TableCell className="text-sm">
                          {item.required_state}
                        </TableCell>
                        <TableCell>{ratingBadge(item.rating)}</TableCell>
                        <TableCell className="hidden lg:table-cell text-sm">
                          {item.recommendation}
                        </TableCell>
                        <TableCell className="hidden md:table-cell text-sm text-muted-foreground">
                          {item.regulatory_reference}
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </CardContent>
            </Card>
          ) : (
            <p className="text-sm text-muted-foreground">No audit items found.</p>
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
