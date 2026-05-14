// Domain types mirroring the Python Pydantic models — PDCA-aligned

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
  | "brief"
  | "short"
  | "medium"
  | "long"
  | "extended";

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

export type SurveillanceType =
  | "audiometry"
  | "spirometry"
  | "skin_check"
  | "havs_questionnaire"
  | "biological_monitoring"
  | "vision_screening"
  | "health_questionnaire"
  | "clinical_examination"
  | "fitness_assessment";

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

export interface HazardProfile {
  category: HazardCategory;
  hazard_phrase: string;
  substance_or_agent?: string;
  exposure_level: ExposureLevel;
  exposure_frequency: ExposureFrequency;
  exposure_duration: ExposureDuration;
  workplace_exposure_limit?: string;
  potential_health_effects?: string;
  existing_controls?: string;
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
  risk_assessment_confirmed: boolean;
  workers_consulted: boolean;
}

// PDCA PLAN
export interface RiskProfileSummary {
  hazard_summary: string;
  risk_assessment_confirmed: boolean;
  workers_consulted: boolean;
  key_risks: string[];
  regulatory_drivers: string[];
}

// PDCA DO
export interface SurveillanceProvision {
  surveillance_type: SurveillanceType;
  description: string;
  frequency: string;
  competence_required: string;
  referral_pathway?: string;
  retention_period?: string;
  regulatory_basis: string;
  delegation_notes?: string;
}

export interface WorkflowStep {
  order: number;
  component: WorkflowComponent;
  description: string;
  responsible_role: string;
  frequency: string;
  regulatory_basis: string;
  delegation_notes?: string;
}

export interface GovernancePrompt {
  prompt_text: string;
  applicable_roles: string[];
  regulatory_reference: string;
}

// PDCA CHECK
export interface AssuranceCheckItem {
  area: string;
  question: string;
  status: ComplianceRating;
  finding?: string;
  recommendation?: string;
  regulatory_reference?: string;
}

export interface TrendInsight {
  area: string;
  observation: string;
  implication: string;
  recommended_action?: string;
}

// PDCA ACT
export interface ImprovementAction {
  area: string;
  action: string;
  rationale: string;
  priority: string;
  regulatory_reference?: string;
}

export interface WorkflowRequest {
  organisation: OrganisationProfile;
  hazards: HazardProfile[];
  additional_context?: string;
}

export interface WorkflowResponse {
  request_id: string;
  generated_at: string;
  organisation_name: string;
  hazard_summary: string;
  risk_profile?: RiskProfileSummary;
  surveillance_provisions: SurveillanceProvision[];
  steps: WorkflowStep[];
  assurance_checks: AssuranceCheckItem[];
  trend_insights: TrendInsight[];
  improvement_actions: ImprovementAction[];
  governance_prompts: GovernancePrompt[];
  sources_cited: string[];
  disclaimers: string[];
  model_used: string;
  knowledge_chunks_used: number;
}

export interface BenchmarkRequest {
  organisation: OrganisationProfile;
  hazards: HazardProfile[];
}

export interface BenchmarkResult {
  request_id: string;
  generated_at: string;
  organisation_name: string;
  areas_assessed: string[];
  compliant_areas: string[];
  non_compliant_areas: string[];
  recommendations: string[];
  sources_cited: string[];
}

export interface GapItem {
  area: string;
  current_state: string;
  required_state: string;
  rating: ComplianceRating;
  recommendation: string;
  regulatory_reference: string;
}

export interface GapAnalysis {
  request_id: string;
  generated_at: string;
  organisation_name: string;
  gaps: GapItem[];
  overall_rating: ComplianceRating;
  sources_cited: string[];
}

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
}
