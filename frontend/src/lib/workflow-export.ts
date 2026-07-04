import type { WorkflowResponse } from "@/lib/types";

function slugifyFilename(name: string): string {
  const slug = name
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "");
  return slug.slice(0, 48) || "workflow";
}

export function workflowExportBasename(workflow: WorkflowResponse): string {
  const date = workflow.generated_at.slice(0, 10);
  return `oh-workflow-${slugifyFilename(workflow.organisation_name)}-${date}`;
}

function triggerDownload(blob: Blob, filename: string): void {
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = filename;
  anchor.rel = "noopener";
  document.body.appendChild(anchor);
  anchor.click();
  anchor.remove();
  URL.revokeObjectURL(url);
}

export function downloadWorkflowJson(workflow: WorkflowResponse): void {
  const blob = new Blob([JSON.stringify(workflow, null, 2)], {
    type: "application/json;charset=utf-8",
  });
  triggerDownload(blob, `${workflowExportBasename(workflow)}.json`);
}

export function workflowToMarkdown(workflow: WorkflowResponse): string {
  const lines: string[] = [
    "# Occupational Health PDCA Workflow",
    "",
    `**Organisation:** ${workflow.organisation_name}`,
    `**Hazards:** ${workflow.hazard_summary}`,
    `**Generated:** ${workflow.generated_at}`,
    `**Request ID:** ${workflow.request_id}`,
    `**Model:** ${workflow.model_used}`,
    "",
  ];

  if (workflow.risk_profile) {
    lines.push("## PLAN — Risk profile", "");
    lines.push(
      `- Risk assessment confirmed: ${workflow.risk_profile.risk_assessment_confirmed ? "Yes" : "No"}`
    );
    lines.push(
      `- Workers consulted: ${workflow.risk_profile.workers_consulted ? "Yes" : "No"}`
    );
    if (workflow.risk_profile.key_risks.length > 0) {
      lines.push("", "**Key risks:**");
      for (const risk of workflow.risk_profile.key_risks) {
        lines.push(`- ${risk}`);
      }
    }
    if (workflow.risk_profile.regulatory_drivers.length > 0) {
      lines.push("", "**Regulatory drivers:**");
      for (const driver of workflow.risk_profile.regulatory_drivers) {
        lines.push(`- ${driver}`);
      }
    }
    lines.push("");
  }

  if (workflow.surveillance_provisions.length > 0) {
    lines.push("## DO — Surveillance provisions", "");
    workflow.surveillance_provisions.forEach((sp, i) => {
      lines.push(`### ${i + 1}. ${sp.surveillance_type.replace(/_/g, " ")}`, "");
      lines.push(`- **Description:** ${sp.description}`);
      lines.push(`- **Frequency:** ${sp.frequency}`);
      lines.push(`- **Competence:** ${sp.competence_required}`);
      if (sp.referral_pathway) lines.push(`- **Referral:** ${sp.referral_pathway}`);
      if (sp.retention_period) lines.push(`- **Retention:** ${sp.retention_period}`);
      lines.push(`- **Regulatory basis:** ${sp.regulatory_basis}`);
      if (sp.delegation_notes) lines.push(`- **Delegation:** ${sp.delegation_notes}`);
      lines.push("");
    });
  }

  if (workflow.steps.length > 0) {
    lines.push("## DO — Workflow steps", "");
    for (const step of workflow.steps) {
      lines.push(
        `### Step ${step.order}: ${step.component.replace(/_/g, " ")}${step.pdca_phase ? ` (${step.pdca_phase.toUpperCase()})` : ""}`,
        "",
        `- **Description:** ${step.description}`,
        `- **Responsible role:** ${step.responsible_role}`,
        `- **Frequency:** ${step.frequency}`,
        `- **Regulatory basis:** ${step.regulatory_basis}`,
        ...(step.delegation_notes ? [`- **Delegation:** ${step.delegation_notes}`] : []),
        ""
      );
    }
  }

  if (workflow.governance_prompts.length > 0) {
    lines.push("## DO — Governance prompts", "");
    for (const gp of workflow.governance_prompts) {
      lines.push(`- ${gp.prompt_text} *(Roles: ${gp.applicable_roles.join(", ")}; ${gp.regulatory_reference})*`);
    }
    lines.push("");
  }

  if (workflow.assurance_checks.length > 0) {
    lines.push("## CHECK — Assurance checks", "");
    for (const ac of workflow.assurance_checks) {
      lines.push(`### ${ac.area}`, "");
      lines.push(`- **Question:** ${ac.question}`);
      lines.push(`- **Status:** ${ac.status.replace(/_/g, " ")}`);
      if (ac.recommendation) lines.push(`- **Recommendation:** ${ac.recommendation}`);
      if (ac.regulatory_reference) lines.push(`- **Regulation:** ${ac.regulatory_reference}`);
      lines.push("");
    }
  }

  if (workflow.trend_insights.length > 0) {
    lines.push("## CHECK — Trend insights", "");
    for (const ti of workflow.trend_insights) {
      lines.push(`### ${ti.area}`, "");
      lines.push(`- **Observation:** ${ti.observation}`);
      lines.push(`- **Implication:** ${ti.implication}`);
      if (ti.recommended_action) lines.push(`- **Action:** ${ti.recommended_action}`);
      lines.push("");
    }
  }

  if (workflow.improvement_actions.length > 0) {
    lines.push("## ACT — Improvement actions", "");
    for (const ia of workflow.improvement_actions) {
      lines.push(
        `- **[${ia.priority}] ${ia.area}:** ${ia.action} — ${ia.rationale}${ia.regulatory_reference ? ` (${ia.regulatory_reference})` : ""}`
      );
    }
    lines.push("");
  }

  if (workflow.sources_cited.length > 0) {
    lines.push("## Sources cited", "");
    for (const source of workflow.sources_cited) {
      lines.push(`- ${source}`);
    }
    lines.push("");
  }

  if (workflow.disclaimers.length > 0) {
    lines.push("## Important notices", "");
    for (const disclaimer of workflow.disclaimers) {
      if (disclaimer.trim()) lines.push(`- ${disclaimer.trim()}`);
    }
    lines.push("");
  }

  return lines.join("\n");
}

export function downloadWorkflowMarkdown(workflow: WorkflowResponse): void {
  const blob = new Blob([workflowToMarkdown(workflow)], {
    type: "text/markdown;charset=utf-8",
  });
  triggerDownload(blob, `${workflowExportBasename(workflow)}.md`);
}
