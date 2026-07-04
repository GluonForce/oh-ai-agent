/** Backend URL for browser requests (requires CORS on the API). */
export function resolveApiBase(): string {
  return process.env.NEXT_PUBLIC_API_URL?.replace(/\/$/, "") || "http://localhost:8000";
}

export const API_BASE = resolveApiBase();

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const headers = new Headers(options?.headers);
  if (options?.body != null && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }

  const res = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers,
  });
  if (!res.ok) {
    const body = await res.text();
    throw new Error(`API ${res.status}: ${body}`);
  }
  return res.json() as Promise<T>;
}

// --- System ---
import type {
  AuditEntry,
  BenchmarkRequest,
  BenchmarkResult,
  ComplianceAuditRequest,
  ComplianceAuditResponse,
  GapAnalysis,
  HealthResponse,
  ImprovementPlanRequest,
  ImprovementPlanResponse,
  InfoResponse,
  IngestResponse,
  KnowledgeSource,
  KnowledgeStats,
  TrendAnalysisRequest,
  TrendAnalysisResponse,
  WorkflowRequest,
  WorkflowResponse,
} from "./types";

export const api = {
  health: () => request<HealthResponse>("/health"),
  info: () => request<InfoResponse>("/info"),

  generateWorkflow: (data: WorkflowRequest) =>
    request<WorkflowResponse>("/api/v1/workflows", {
      method: "POST",
      body: JSON.stringify(data),
    }),

  benchmark: (data: BenchmarkRequest) =>
    request<BenchmarkResult>("/api/v1/benchmark", {
      method: "POST",
      body: JSON.stringify(data),
    }),

  gapAnalysis: (data: BenchmarkRequest) =>
    request<GapAnalysis>("/api/v1/gap-analysis", {
      method: "POST",
      body: JSON.stringify(data),
    }),

  knowledgeSources: () =>
    request<KnowledgeSource[]>("/api/v1/knowledge/sources"),

  knowledgeStats: () =>
    request<KnowledgeStats>("/api/v1/knowledge/stats"),

  ingestKnowledge: () =>
    request<IngestResponse>("/api/v1/knowledge/ingest", { method: "POST" }),

  uploadDocument: async (file: File): Promise<IngestResponse> => {
    const form = new FormData();
    form.append("file", file);
    const res = await fetch(`${API_BASE}/api/v1/knowledge/upload`, {
      method: "POST",
      body: form,
    });
    if (!res.ok) throw new Error(`Upload failed: ${res.status}`);
    return res.json() as Promise<IngestResponse>;
  },

  auditTrail: (limit = 100) =>
    request<AuditEntry[]>(`/api/v1/audit?limit=${limit}`),

  auditCount: () =>
    request<{ total_entries: number }>("/api/v1/audit/count"),

  complianceAudit: (data: ComplianceAuditRequest) =>
    request<ComplianceAuditResponse>("/api/v1/compliance-audit", {
      method: "POST",
      body: JSON.stringify(data),
    }),

  trendAnalysis: (data: TrendAnalysisRequest) =>
    request<TrendAnalysisResponse>("/api/v1/trend-analysis", {
      method: "POST",
      body: JSON.stringify(data),
    }),

  improvementPlan: (data: ImprovementPlanRequest) =>
    request<ImprovementPlanResponse>("/api/v1/improvement-plan", {
      method: "POST",
      body: JSON.stringify(data),
    }),
};
