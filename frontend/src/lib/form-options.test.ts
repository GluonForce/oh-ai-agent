import { describe, expect, it } from "vitest";
import {
  CONTROL_MEASURE_OPTIONS,
  EXPOSURE_FREQUENCY_DEFINITIONS,
  EXPOSURE_LEVEL_DEFINITIONS,
  PRE_EXISTING_CONDITION_OPTIONS,
  SECTOR_OPTIONS,
  WET_WORK_HIGH_RISK_HAND_WASHES,
  isWetWorkHazard,
  joinSelections,
  splitSelections,
  suggestHealthEffects,
  suggestSurveillanceLevel,
  suggestWel,
  tasksForSector,
} from "./form-options";
import { parseSourceCitation } from "./resource-links";

describe("form-options", () => {
  it("maps sector keys to task catalogs", () => {
    for (const sector of SECTOR_OPTIONS) {
      expect(Array.isArray(tasksForSector(sector.value))).toBe(true);
    }
    expect(tasksForSector("manufacturing")).toContain("Welding");
    expect(tasksForSector("unknown-sector")).toEqual([]);
  });

  it("joins and splits selections including Other", () => {
    const joined = joinSelections(["Shift / night workers"], "Contractors");
    expect(joined).toBe("Shift / night workers; Contractors");
    const split = splitSelections(joined, ["Shift / night workers"]);
    expect(split.selected).toEqual(["Shift / night workers"]);
    expect(split.other).toBe("Contractors");
  });

  it("covers exposure level and frequency definitions", () => {
    expect(Object.keys(EXPOSURE_LEVEL_DEFINITIONS).sort()).toEqual(
      ["high", "low", "moderate", "negligible", "very_high"].sort()
    );
    expect(Object.keys(EXPOSURE_FREQUENCY_DEFINITIONS).sort()).toEqual(
      ["continuous", "frequent", "occasional", "rare"].sort()
    );
  });

  it("suggests WEL and health effects from agent/category", () => {
    expect(suggestWel("isocyanates")).toMatch(/NCO/);
    expect(suggestWel("noise", "noise")).toMatch(/dB/);
    expect(suggestHealthEffects("noise")).toContain("NIHL");
    expect(suggestHealthEffects("chemical", "isocyanates")).toContain("asthma");
  });

  it("orders controls by hierarchy of controls", () => {
    expect(CONTROL_MEASURE_OPTIONS[0]).toBe("Elimination");
    expect(CONTROL_MEASURE_OPTIONS.at(-1)).toMatch(/PPE/);
    expect(CONTROL_MEASURE_OPTIONS.some((c) => c.includes("Health surveillance"))).toBe(true);
  });

  it("detects wet work and surveillance level threshold", () => {
    expect(isWetWorkHazard("skin")).toBe(true);
    expect(isWetWorkHazard("chemical", "Wet work / skin irritants")).toBe(true);
    expect(suggestSurveillanceLevel(WET_WORK_HIGH_RISK_HAND_WASHES + 1)).toBe("higher");
    expect(suggestSurveillanceLevel(10)).toBe("lower");
    expect(PRE_EXISTING_CONDITION_OPTIONS.some((c) => c.includes("Asthma"))).toBe(true);
  });
});

describe("parseSourceCitation", () => {
  it("extracts title and URL from model citation strings", () => {
    const parsed = parseSourceCitation(
      "Health Surveillance at Work — Key Requirements (Summary based on HSG61) — https://www.hse.gov.uk/health-surveillance/"
    );
    expect(parsed.url).toBe("https://www.hse.gov.uk/health-surveillance/");
    expect(parsed.title).toContain("Health Surveillance at Work");
  });

  it("keeps plain text when no URL is present", () => {
    const parsed = parseSourceCitation("COSHH Regulation 11");
    expect(parsed.url).toBeNull();
    expect(parsed.title).toBe("COSHH Regulation 11");
  });
});
