const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

async function request<T>(
  path: string,
  options?: RequestInit
): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { "Content-Type": "application/json", ...options?.headers },
    ...options,
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
  GapAnalysis,
  HealthResponse,
  InfoResponse,
  IngestResponse,
  KnowledgeSource,
  KnowledgeStats,
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
};
