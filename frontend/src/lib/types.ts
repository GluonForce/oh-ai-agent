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

export interface HazardProfile {
  category: HazardCategory;
  hazard_phrase: string;
  substance_or_agent?: string;
  exposure_level: ExposureLevel;
  exposure_frequency: ExposureFrequency;
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
  steps: WorkflowStep[];
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
