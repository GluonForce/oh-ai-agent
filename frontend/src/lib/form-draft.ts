/**
 * Live draft (sessionStorage) + named history (localStorage) for org/hazard forms.
 */

import type {
  HazardProfile,
  OrganisationProfile,
  RiskAssessmentConfirmation,
} from "@/lib/types";

export const LIVE_DRAFT_KEY = "oh-agent:live-draft";
export const NAMED_DRAFTS_KEY = "oh-agent:named-drafts";

export interface FormDraftPayload {
  org: OrganisationProfile;
  hazards: HazardProfile[];
  tasksText: string;
  additionalContext: string;
  riskAssessment: RiskAssessmentConfirmation;
  updatedAt: string;
}

export interface NamedDraft {
  id: string;
  name: string;
  payload: FormDraftPayload;
  savedAt: string;
}

export type StorageLike = Pick<Storage, "getItem" | "setItem" | "removeItem">;

function safeParse<T>(raw: string | null): T | null {
  if (!raw) return null;
  try {
    return JSON.parse(raw) as T;
  } catch {
    return null;
  }
}

export function loadLiveDraft(
  storage: StorageLike = typeof sessionStorage !== "undefined" ? sessionStorage : createMemoryStorage()
): FormDraftPayload | null {
  return safeParse<FormDraftPayload>(storage.getItem(LIVE_DRAFT_KEY));
}

export function saveLiveDraft(
  payload: Omit<FormDraftPayload, "updatedAt">,
  storage: StorageLike = typeof sessionStorage !== "undefined" ? sessionStorage : createMemoryStorage()
): FormDraftPayload {
  const full: FormDraftPayload = {
    ...payload,
    updatedAt: new Date().toISOString(),
  };
  storage.setItem(LIVE_DRAFT_KEY, JSON.stringify(full));
  return full;
}

export function clearLiveDraft(
  storage: StorageLike = typeof sessionStorage !== "undefined" ? sessionStorage : createMemoryStorage()
): void {
  storage.removeItem(LIVE_DRAFT_KEY);
}

export function listNamedDrafts(
  storage: StorageLike = typeof localStorage !== "undefined" ? localStorage : createMemoryStorage()
): NamedDraft[] {
  const list = safeParse<NamedDraft[]>(storage.getItem(NAMED_DRAFTS_KEY));
  if (!Array.isArray(list)) return [];
  return list.sort((a, b) => b.savedAt.localeCompare(a.savedAt));
}

export function saveNamedDraft(
  name: string,
  payload: Omit<FormDraftPayload, "updatedAt">,
  storage: StorageLike = typeof localStorage !== "undefined" ? localStorage : createMemoryStorage()
): NamedDraft {
  const drafts = listNamedDrafts(storage);
  const draft: NamedDraft = {
    id: `${Date.now()}-${Math.random().toString(36).slice(2, 8)}`,
    name: name.trim() || "Untitled draft",
    payload: { ...payload, updatedAt: new Date().toISOString() },
    savedAt: new Date().toISOString(),
  };
  drafts.unshift(draft);
  storage.setItem(NAMED_DRAFTS_KEY, JSON.stringify(drafts.slice(0, 20)));
  return draft;
}

export function loadNamedDraft(
  id: string,
  storage: StorageLike = typeof localStorage !== "undefined" ? localStorage : createMemoryStorage()
): NamedDraft | null {
  return listNamedDrafts(storage).find((d) => d.id === id) ?? null;
}

export function deleteNamedDraft(
  id: string,
  storage: StorageLike = typeof localStorage !== "undefined" ? localStorage : createMemoryStorage()
): void {
  const next = listNamedDrafts(storage).filter((d) => d.id !== id);
  storage.setItem(NAMED_DRAFTS_KEY, JSON.stringify(next));
}

/** In-memory Storage for tests / SSR. */
export function createMemoryStorage(initial: Record<string, string> = {}): StorageLike {
  const map = new Map<string, string>(Object.entries(initial));
  return {
    getItem: (key) => map.get(key) ?? null,
    setItem: (key, value) => {
      map.set(key, value);
    },
    removeItem: (key) => {
      map.delete(key);
    },
  };
}
