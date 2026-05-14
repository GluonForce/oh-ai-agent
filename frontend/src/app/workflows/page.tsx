"use client";

import { useState } from "react";
import {
  AlertTriangle,
  CheckCircle2,
  ClipboardCheck,
  FileText,
  ShieldAlert,
} from "lucide-react";
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
  WorkflowResponse,
} from "@/lib/types";
import { toast } from "sonner";

const COMPONENT_LABELS: Record<string, string> = {
  health_questionnaire: "Health Questionnaire",
  clinical_assessment: "Clinical Assessment",
  biological_monitoring: "Biological Monitoring",
  lung_function_test: "Lung Function Test",
  audiometry: "Audiometry",
  skin_assessment: "Skin Assessment",
  vision_screening: "Vision Screening",
  fitness_for_task: "Fitness for Task",
  health_education: "Health Education",
  referral: "Referral",
  review_appointment: "Review Appointment",
  record_keeping: "Record Keeping",
};

export default function WorkflowsPage() {
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<WorkflowResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (
    org: OrganisationProfile,
    hazards: HazardProfile[],
    additionalContext?: string
  ) => {
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const res = await api.generateWorkflow({
        organisation: org,
        hazards,
        additional_context: additionalContext,
      });
      setResult(res);
      toast.success("Workflow generated successfully");
    } catch (e) {
      const msg = e instanceof Error ? e.message : "Unknown error";
      setError(msg);
      toast.error("Failed to generate workflow");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6 max-w-4xl">
      <div>
        <h1 className="text-2xl font-bold flex items-center gap-2">
          <ClipboardCheck className="h-6 w-6" />
          Workflow Generator
        </h1>
        <p className="text-muted-foreground mt-1">
          Generate hazard-specific, risk-profiled occupational health workflows
          aligned to UK regulatory requirements.
        </p>
      </div>

      <OrgHazardForm
        submitLabel="Generate Workflow"
        loading={loading}
        showAdditionalContext
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
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between flex-wrap gap-2">
                <CardTitle className="text-base flex items-center gap-2">
                  <FileText className="h-4 w-4" />
                  Generated Workflow
                </CardTitle>
                <div className="flex gap-2 flex-wrap">
                  <Badge variant="outline">{result.model_used}</Badge>
                  <Badge variant="secondary">
                    {result.knowledge_chunks_used} knowledge chunks
                  </Badge>
                  <Badge variant="secondary">
                    {result.steps.length} steps
                  </Badge>
                </div>
              </div>
              <p className="text-sm text-muted-foreground mt-1">
                {result.organisation_name} — {result.hazard_summary}
              </p>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead className="w-12">#</TableHead>
                    <TableHead>Component</TableHead>
                    <TableHead className="hidden lg:table-cell">
                      Description
                    </TableHead>
                    <TableHead>Role</TableHead>
                    <TableHead>Frequency</TableHead>
                    <TableHead className="hidden md:table-cell">
                      Regulatory Basis
                    </TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {result.steps.map((step) => (
                    <TableRow key={step.order}>
                      <TableCell className="font-medium">
                        {step.order}
                      </TableCell>
                      <TableCell>
                        <Badge variant="outline">
                          {COMPONENT_LABELS[step.component] || step.component}
                        </Badge>
                      </TableCell>
                      <TableCell className="hidden lg:table-cell text-sm">
                        {step.description}
                      </TableCell>
                      <TableCell className="text-sm">
                        {step.responsible_role}
                      </TableCell>
                      <TableCell className="text-sm">
                        {step.frequency}
                      </TableCell>
                      <TableCell className="hidden md:table-cell text-sm text-muted-foreground">
                        {step.regulatory_basis}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </CardContent>
          </Card>

          {result.governance_prompts.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle className="text-base flex items-center gap-2">
                  <ShieldAlert className="h-4 w-4" />
                  Governance Prompts
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                {result.governance_prompts.map((gp, i) => (
                  <div key={i} className="border-l-2 border-amber-500 pl-3">
                    <p className="text-sm">{gp.prompt_text}</p>
                    <p className="text-xs text-muted-foreground mt-1">
                      Roles: {gp.applicable_roles.join(", ")} | Ref:{" "}
                      {gp.regulatory_reference}
                    </p>
                  </div>
                ))}
              </CardContent>
            </Card>
          )}

          {result.sources_cited.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle className="text-base flex items-center gap-2">
                  <CheckCircle2 className="h-4 w-4" />
                  Sources Cited
                </CardTitle>
              </CardHeader>
              <CardContent>
                <ul className="space-y-1">
                  {result.sources_cited.map((s, i) => (
                    <li key={i} className="text-sm text-muted-foreground">
                      • {s}
                    </li>
                  ))}
                </ul>
              </CardContent>
            </Card>
          )}
        </div>
      )}
    </div>
  );
}
