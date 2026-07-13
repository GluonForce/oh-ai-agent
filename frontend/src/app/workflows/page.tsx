"use client";

import { useState } from "react";
import {
  AlertTriangle,
  ArrowUpCircle,
  CheckCircle2,
  ClipboardCheck,
  Download,
  FileText,
  ListChecks,
  ShieldAlert,
  Stethoscope,
  TrendingUp,
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Separator } from "@/components/ui/separator";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { OrgHazardForm } from "@/components/org-hazard-form";
import { api } from "@/lib/api";
import { downloadWorkflowJson, downloadWorkflowMarkdown } from "@/lib/workflow-export";
import type {
  HazardProfile,
  OrganisationProfile,
  RiskAssessmentConfirmation,
  WorkflowResponse,
  ComplianceRating,
} from "@/lib/types";
import { toast } from "sonner";

const SURVEILLANCE_LABELS: Record<string, string> = {
  audiometry: "Audiometry",
  spirometry: "Spirometry",
  skin_check: "Skin Check",
  havs_questionnaire: "HAVS Questionnaire",
  biological_monitoring: "Biological Monitoring",
  vision_screening: "Vision Screening",
  health_questionnaire: "Health Questionnaire",
  clinical_examination: "Clinical Examination",
  fitness_assessment: "Fitness Assessment",
};

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

export default function WorkflowsPage() {
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<WorkflowResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (
    org: OrganisationProfile,
    hazards: HazardProfile[],
    additionalContext?: string,
    riskAssessment?: RiskAssessmentConfirmation
  ) => {
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const res = await api.generateWorkflow({
        organisation: org,
        hazards,
        additional_context: additionalContext,
        risk_assessment: riskAssessment ?? {
          risk_assessment_completed: false,
          workers_consulted: false,
        },
      });
      setResult(res);
      toast.success("PDCA workflow generated successfully");
    } catch (e) {
      const msg = e instanceof Error ? e.message : "Unknown error";
      setError(msg);
      toast.error("Failed to generate workflow");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6 max-w-5xl">
      <div>
        <h1 className="text-2xl font-bold flex items-center gap-2">
          <ClipboardCheck className="h-6 w-6" />
          PDCA Workflow Generator
        </h1>
        <p className="text-muted-foreground mt-1">
          Generate hazard-specific, risk-profiled occupational health workflows
          structured around Plan-Do-Check-Act, aligned to UK regulatory
          requirements.
        </p>
      </div>

      <OrgHazardForm
        submitLabel="Generate PDCA Workflow"
        loading={loading}
        showAdditionalContext
        showRiskAssessment
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
            <h2 className="text-lg font-semibold flex items-center gap-2">
              <FileText className="h-5 w-5" />
              Generated PDCA Workflow
            </h2>
            <div className="flex gap-2 flex-wrap items-center">
              <DropdownMenu>
                <DropdownMenuTrigger
                  className="inline-flex h-8 items-center justify-center gap-1.5 rounded-lg border border-input bg-background px-2.5 text-sm font-medium hover:bg-muted"
                >
                  <Download className="h-4 w-4" />
                  Download
                </DropdownMenuTrigger>
                <DropdownMenuContent align="end">
                  <DropdownMenuItem
                    onClick={() => {
                      downloadWorkflowMarkdown(result);
                      toast.success("Workflow downloaded as Markdown");
                    }}
                  >
                    Markdown (.md)
                  </DropdownMenuItem>
                  <DropdownMenuItem
                    onClick={() => {
                      downloadWorkflowJson(result);
                      toast.success("Workflow downloaded as JSON");
                    }}
                  >
                    JSON (.json)
                  </DropdownMenuItem>
                </DropdownMenuContent>
              </DropdownMenu>
              <Badge variant="outline">{result.model_used}</Badge>
              <Badge variant="secondary">
                {result.knowledge_chunks_used} knowledge chunks
              </Badge>
            </div>
          </div>
          <p className="text-sm text-muted-foreground">
            {result.organisation_name} — {result.hazard_summary}
          </p>

          <Tabs defaultValue="plan">
            <TabsList>
              <TabsTrigger value="plan">PLAN</TabsTrigger>
              <TabsTrigger value="do">DO</TabsTrigger>
              <TabsTrigger value="check">CHECK</TabsTrigger>
              <TabsTrigger value="act">ACT</TabsTrigger>
            </TabsList>
            <p className="mt-2 text-sm text-muted-foreground">
              Surveillance Provisions = statutory checks &amp; competence requirements. Workflow Steps =
              operational sequence to deliver them.
            </p>

            {/* PLAN */}
            <TabsContent value="plan">
              {result.risk_profile ? (
                <Card>
                  <CardHeader>
                    <CardTitle className="text-base">
                      Risk Profile Summary
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-3">
                    <div className="flex gap-3 flex-wrap">
                      <Badge variant={result.risk_profile.risk_assessment_confirmed ? "default" : "secondary"}>
                        Risk Assessment: {result.risk_profile.risk_assessment_confirmed ? "Confirmed" : "Not Confirmed"}
                      </Badge>
                      <Badge variant={result.risk_profile.workers_consulted ? "default" : "secondary"}>
                        Workers Consulted: {result.risk_profile.workers_consulted ? "Yes" : "No"}
                      </Badge>
                    </div>
                    {result.risk_profile.key_risks.length > 0 && (
                      <div>
                        <p className="text-sm font-medium mb-1">Key Risks</p>
                        <ul className="space-y-1">
                          {result.risk_profile.key_risks.map((r, i) => (
                            <li key={i} className="text-sm text-muted-foreground">• {r}</li>
                          ))}
                        </ul>
                      </div>
                    )}
                    {result.risk_profile.regulatory_drivers.length > 0 && (
                      <div>
                        <p className="text-sm font-medium mb-1">Regulatory Drivers</p>
                        <div className="flex flex-wrap gap-2">
                          {result.risk_profile.regulatory_drivers.map((d, i) => (
                            <Badge key={i} variant="outline">{d}</Badge>
                          ))}
                        </div>
                      </div>
                    )}
                  </CardContent>
                </Card>
              ) : (
                <p className="text-sm text-muted-foreground p-4">
                  No risk profile data in this response.
                </p>
              )}
            </TabsContent>

            {/* DO */}
            <TabsContent value="do" className="space-y-4">
              {result.surveillance_provisions.length > 0 && (
                <Card>
                  <CardHeader>
                    <CardTitle className="text-base flex items-center gap-2">
                      <Stethoscope className="h-4 w-4" />
                      Surveillance Provisions
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="p-0">
                    <Table>
                      <TableHeader>
                        <TableRow>
                          <TableHead>Type</TableHead>
                          <TableHead className="hidden lg:table-cell">Description</TableHead>
                          <TableHead>Frequency</TableHead>
                          <TableHead className="hidden md:table-cell">Competence</TableHead>
                          <TableHead className="hidden xl:table-cell">Referral</TableHead>
                          <TableHead className="hidden xl:table-cell">Retention</TableHead>
                          <TableHead className="hidden md:table-cell">Regulation</TableHead>
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        {result.surveillance_provisions.map((sp, i) => (
                          <TableRow key={i}>
                            <TableCell>
                              <Badge variant="outline">
                                {SURVEILLANCE_LABELS[sp.surveillance_type] || sp.surveillance_type}
                              </Badge>
                            </TableCell>
                            <TableCell className="hidden lg:table-cell text-sm">{sp.description}</TableCell>
                            <TableCell className="text-sm">{sp.frequency}</TableCell>
                            <TableCell className="hidden md:table-cell text-sm">{sp.competence_required}</TableCell>
                            <TableCell className="hidden xl:table-cell text-sm text-muted-foreground">{sp.referral_pathway || "—"}</TableCell>
                            <TableCell className="hidden xl:table-cell text-sm text-muted-foreground">{sp.retention_period || "—"}</TableCell>
                            <TableCell className="hidden md:table-cell text-sm text-muted-foreground">{sp.regulatory_basis}</TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  </CardContent>
                </Card>
              )}

              {result.steps.length > 0 && (
                <Card>
                  <CardHeader>
                    <CardTitle className="text-base flex items-center gap-2">
                      <ListChecks className="h-4 w-4" />
                      Workflow Steps ({result.steps.length})
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="p-0">
                    <Table>
                      <TableHeader>
                        <TableRow>
                          <TableHead className="w-12">#</TableHead>
                          <TableHead>Component</TableHead>
                          <TableHead>Phase</TableHead>
                          <TableHead className="hidden lg:table-cell">Description</TableHead>
                          <TableHead>Role</TableHead>
                          <TableHead>Frequency</TableHead>
                          <TableHead className="hidden md:table-cell">Regulatory Basis</TableHead>
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        {result.steps.map((step) => (
                          <TableRow key={step.order}>
                            <TableCell className="font-medium">{step.order}</TableCell>
                            <TableCell>
                              <Badge variant="outline">
                                {COMPONENT_LABELS[step.component] || step.component}
                              </Badge>
                            </TableCell>
                            <TableCell>
                              {step.pdca_phase && (
                                <Badge variant="secondary" className="uppercase text-xs">
                                  {step.pdca_phase}
                                </Badge>
                              )}
                            </TableCell>
                            <TableCell className="hidden lg:table-cell text-sm">{step.description}</TableCell>
                            <TableCell className="text-sm">{step.responsible_role}</TableCell>
                            <TableCell className="text-sm">{step.frequency}</TableCell>
                            <TableCell className="hidden md:table-cell text-sm text-muted-foreground">{step.regulatory_basis}</TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  </CardContent>
                </Card>
              )}

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
            </TabsContent>

            {/* CHECK */}
            <TabsContent value="check" className="space-y-4">
              {result.assurance_checks.length > 0 && (
                <Card>
                  <CardHeader>
                    <CardTitle className="text-base flex items-center gap-2">
                      <CheckCircle2 className="h-4 w-4" />
                      Assurance Checks
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="p-0">
                    <Table>
                      <TableHeader>
                        <TableRow>
                          <TableHead>Area</TableHead>
                          <TableHead>Question</TableHead>
                          <TableHead>Status</TableHead>
                          <TableHead className="hidden lg:table-cell">Recommendation</TableHead>
                          <TableHead className="hidden md:table-cell">Regulation</TableHead>
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        {result.assurance_checks.map((ac, i) => (
                          <TableRow key={i}>
                            <TableCell className="font-medium text-sm">{ac.area}</TableCell>
                            <TableCell className="text-sm">{ac.question}</TableCell>
                            <TableCell>{ratingBadge(ac.status)}</TableCell>
                            <TableCell className="hidden lg:table-cell text-sm">{ac.recommendation || "—"}</TableCell>
                            <TableCell className="hidden md:table-cell text-sm text-muted-foreground">{ac.regulatory_reference || "—"}</TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  </CardContent>
                </Card>
              )}

              {result.trend_insights.length > 0 && (
                <Card>
                  <CardHeader>
                    <CardTitle className="text-base flex items-center gap-2">
                      <TrendingUp className="h-4 w-4" />
                      Trend Insights
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-3">
                    {result.trend_insights.map((ti, i) => (
                      <div key={i} className="border-l-2 border-blue-500 pl-3 space-y-1">
                        <p className="text-sm font-medium">{ti.area}</p>
                        <p className="text-sm">{ti.observation}</p>
                        <p className="text-xs text-muted-foreground">
                          Implication: {ti.implication}
                        </p>
                        {ti.recommended_action && (
                          <p className="text-xs text-muted-foreground">
                            Action: {ti.recommended_action}
                          </p>
                        )}
                      </div>
                    ))}
                  </CardContent>
                </Card>
              )}

              {result.assurance_checks.length === 0 && result.trend_insights.length === 0 && (
                <p className="text-sm text-muted-foreground p-4">
                  No CHECK-phase data in this response.
                </p>
              )}
            </TabsContent>

            {/* ACT */}
            <TabsContent value="act" className="space-y-4">
              {result.improvement_actions.length > 0 ? (
                <Card>
                  <CardHeader>
                    <CardTitle className="text-base flex items-center gap-2">
                      <ArrowUpCircle className="h-4 w-4" />
                      Improvement Actions
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
                          <TableHead className="hidden md:table-cell">Regulation</TableHead>
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        {result.improvement_actions.map((ia, i) => (
                          <TableRow key={i}>
                            <TableCell className="font-medium text-sm">{ia.area}</TableCell>
                            <TableCell className="text-sm">{ia.action}</TableCell>
                            <TableCell className="hidden lg:table-cell text-sm">{ia.rationale}</TableCell>
                            <TableCell>
                              <Badge
                                variant="outline"
                                className={
                                  ia.priority === "high"
                                    ? "bg-red-100 text-red-800 border-red-300"
                                    : ia.priority === "medium"
                                      ? "bg-amber-100 text-amber-800 border-amber-300"
                                      : "bg-green-100 text-green-800 border-green-300"
                                }
                              >
                                {ia.priority}
                              </Badge>
                            </TableCell>
                            <TableCell className="hidden md:table-cell text-sm text-muted-foreground">
                              {ia.regulatory_reference || "—"}
                            </TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  </CardContent>
                </Card>
              ) : (
                <p className="text-sm text-muted-foreground p-4">
                  No ACT-phase data in this response.
                </p>
              )}
            </TabsContent>
          </Tabs>

          {result.sources_cited.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle className="text-base flex items-center gap-2">
                  <CheckCircle2 className="h-4 w-4" />
                  Sources Cited
                </CardTitle>
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
