import { describe, expect, it } from "vitest";
import {
  createMemoryStorage,
  deleteNamedDraft,
  listNamedDrafts,
  loadLiveDraft,
  loadNamedDraft,
  saveLiveDraft,
  saveNamedDraft,
} from "./form-draft";
import type { OrganisationProfile, RiskAssessmentConfirmation } from "./types";

const org: OrganisationProfile = {
  name: "Acme",
  sector: "Manufacturing",
  tasks: ["Welding"],
  multi_site: false,
  site_count: 1,
  delivery_model: "mixed",
  risk_assessment_confirmed: true,
  workers_consulted: true,
};

const riskAssessment: RiskAssessmentConfirmation = {
  risk_assessment_completed: true,
  workers_consulted: true,
};

const basePayload = {
  org,
  hazards: [
    {
      category: "noise" as const,
      hazard_phrase: "Noise — Exposure at or above lower exposure action value",
      exposure_level: "high" as const,
      exposure_frequency: "frequent" as const,
      exposure_duration: "long" as const,
    },
  ],
  tasksText: "Welding",
  additionalContext: "",
  riskAssessment,
};

describe("form-draft", () => {
  it("round-trips live draft and recovers from invalid JSON", () => {
    const storage = createMemoryStorage();
    const saved = saveLiveDraft(basePayload, storage);
    expect(saved.updatedAt).toBeTruthy();
    expect(loadLiveDraft(storage)?.org.name).toBe("Acme");

    storage.setItem("oh-agent:live-draft", "{not-json");
    expect(loadLiveDraft(storage)).toBeNull();
  });

  it("saves, loads, overwrites list, and deletes named drafts", () => {
    const storage = createMemoryStorage();
    const a = saveNamedDraft("First", basePayload, storage);
    const b = saveNamedDraft("Second", basePayload, storage);
    expect(listNamedDrafts(storage).map((d) => d.name)).toEqual(["Second", "First"]);
    expect(loadNamedDraft(a.id, storage)?.name).toBe("First");
    deleteNamedDraft(b.id, storage);
    expect(listNamedDrafts(storage)).toHaveLength(1);
    expect(listNamedDrafts(storage)[0].id).toBe(a.id);
  });
});
