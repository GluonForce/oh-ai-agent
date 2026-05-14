// Domain types mirroring the Python Pydantic models

export type HazardCategory =
  | "chemical"
  | "biological"
  | "physical"
  | "ergonomic"
  | "psychosocial"
  | "noise"
  | "vibration"
  | "radiation"
  | "dust"
  | "skin";

export type ExposureLevel =
  | "negligible"
  | "low"
  | "moderate"
  | "high"
  | "very_high";

export type ExposureFrequency =
  | "rare"
  | "occasional"
  | "frequent"
  | "continuous";

export type ExposureDuration =
  | "short_term"
  | "medium_term"
  | "long_term"
  | "career_length";

export type PDCAPhase = "plan" | "do" | "check" | "act";

export type SurveillanceType =
  | "biological_monitoring"
  | "clinical_assessment"
  | "questionnaire"
  | "lung_function"
  | "audiometry"
  | "skin_check"
  | "vision_test"
  | "fitness_assessment";

export type DeliveryModel = "ohp_led" | "ohn_led" | "technician" | "mixed";

export type WorkflowComponent =
  | "health_questionnaire"
  | "clinical_assessment"
  | "biological_monitoring"
  | "lung_function_test"
  | "audiometry"
  | "skin_assessment"
  | "vision_screening"
  | "fitness_for_task"
  | "health_education"
  | "referral"
  | "review_appointment"
  | "record_keeping";

export type ComplianceRating =
  | "compliant"
  | "partially_compliant"
  | "non_compliant"
  | "not_assessed";

export type AuditEventType =
  | "workflow_requested"
  | "workflow_generated"
  | "benchmark_requested"
  | "benchmark_generated"
  | "gap_analysis_requested"
  | "gap_analysis_generated"
  | "knowledge_retrieved"
  | "document_ingested"
  | "guardrail_triggered"
  | "error";

export interface RiskAssessmentConfirmation {
  risk_assessment_completed: boolean;
  workers_consulted: boolean;
  risk_assessment_date?: string;
  assessor_name?: string;
  additional_notes?: string;
}

export interface HazardProfile {
  category: HazardCategory;
  hazard_phrase: string;
  substance_or_agent?: string;
  exposure_level: ExposureLevel;
  exposure_frequency: ExposureFrequency;
  exposure_duration?: ExposureDuration;
  potential_health_effects?: string;
  existing_controls?: string;
  workplace_exposure_limit?: string;
  notes?: string;
}

export interface OrganisationProfile {
  name: string;
  sector: string;
  tasks: string[];
  workforce_size?: number;
  workforce_characteristics?: string;
  multi_site: boolean;
  site_count: number;
  delivery_model: DeliveryModel;
  existing_surveillance?: string;
}

export interface SurveillanceRequirement {
  surveillance_type: SurveillanceType;
  description: string;
  frequency: string;
  competence_required: string;
  referral_pathway: string;
  retention_period: string;
  regulatory_basis: string;
}

export interface WorkflowStep {
  order: number;
  component: WorkflowComponent;
  description: string;
  responsible_role: string;
  frequency: string;
  regulatory_basis: string;
  delegation_notes?: string;
  pdca_phase?: PDCAPhase;
}

export interface GovernancePrompt {
  prompt_text: string;
  applicable_roles: string[];
  regulatory_reference: string;
}

export interface WorkflowRequest {
  organisation: OrganisationProfile;
  hazards: HazardProfile[];
  additional_context?: string;
  risk_assessment: RiskAssessmentConfirmation;
}

export interface WorkflowResponse {
  request_id: string;
  generated_at: string;
  organisation_name: string;
  hazard_summary: string;
  steps: WorkflowStep[];
  governance_prompts: GovernancePrompt[];
  sources_cited: string[];
  disclaimers: string[];
  model_used: string;
  knowledge_chunks_used: number;
  surveillance_requirements?: SurveillanceRequirement[];
  risk_assessment_confirmed?: boolean;
  workers_consulted?: boolean;
}

// --- Compliance Audit (CHECK) ---

export interface ComplianceAuditItem {
  area: string;
  question: string;
  current_state: string;
  required_state: string;
  rating: ComplianceRating;
  recommendation: string;
  regulatory_reference: string;
}

export interface ComplianceAuditRequest {
  organisation: OrganisationProfile;
  hazards: HazardProfile[];
}

export interface ComplianceAuditResponse {
  request_id: string;
  generated_at: string;
  organisation_name: string;
  audit_items: ComplianceAuditItem[];
  overall_rating: ComplianceRating;
  employee_coverage_assessed: boolean;
  interval_adherence_assessed: boolean;
  governance_assessed: boolean;
  sources_cited: string[];
  model_used: string;
}

// --- Trend Analysis (REVIEW) ---

export interface TrendFinding {
  category: string;
  description: string;
  affected_area: string;
  severity: string;
  recommended_action: string;
  regulatory_reference: string;
}

export interface TrendAnalysisRequest {
  organisation: OrganisationProfile;
  hazards: HazardProfile[];
  surveillance_summary: string;
}

export interface TrendAnalysisResponse {
  request_id: string;
  generated_at: string;
  organisation_name: string;
  findings: TrendFinding[];
  control_effectiveness_indicators: string[];
  sources_cited: string[];
  model_used: string;
}

// --- Improvement Plan (ACT) ---

export interface ImprovementAction {
  action_type: string;
  description: string;
  priority: string;
  regulatory_basis: string;
  expected_outcome: string;
}

export interface ImprovementPlanRequest {
  organisation: OrganisationProfile;
  hazards: HazardProfile[];
  surveillance_findings: string;
}

export interface ImprovementPlanResponse {
  request_id: string;
  generated_at: string;
  organisation_name: string;
  actions: ImprovementAction[];
  management_review_items: string[];
  sources_cited: string[];
  model_used: string;
}

// --- Knowledge & Audit ---

export interface KnowledgeSource {
  id: string;
  title: string;
  source_type: string;
  url?: string;
  publication_date?: string;
  authority: string;
  version?: string;
  description?: string;
}

export interface KnowledgeStats {
  total_chunks: number;
  sources_registered: number;
}

export interface IngestResponse {
  chunks_ingested: number;
  message: string;
}

export interface AuditEntry {
  id: string;
  timestamp: string;
  event_type: AuditEventType;
  request_id?: string;
  actor: string;
  detail: Record<string, unknown>;
  sources_used: string[];
  model_used?: string;
  guardrails_applied: string[];
}

export interface HealthResponse {
  status: string;
  environment: string;
  knowledge_chunks: number;
  audit_entries: number;
}

export interface InfoResponse {
  name: string;
  version: string;
  llm_model: string;
  disclaimers: string[];
  framework?: string;
}
