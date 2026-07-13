/**
 * Static catalogs and helpers for the org/hazard form (feedback-driven UX).
 */

import type {
  ExposureFrequency,
  ExposureLevel,
  HazardCategory,
} from "@/lib/types";

export type Option = { value: string; label: string };

export const SECTOR_OPTIONS: Option[] = [
  { value: "manufacturing", label: "Manufacturing" },
  { value: "construction", label: "Construction" },
  { value: "nhs", label: "NHS / Healthcare" },
  { value: "transport", label: "Transport & Logistics" },
  { value: "agriculture", label: "Agriculture" },
  { value: "education", label: "Education" },
  { value: "local_authority", label: "Local Authority" },
  { value: "energy", label: "Energy / Utilities" },
  { value: "hospitality", label: "Hospitality" },
  { value: "other", label: "Other" },
];

/** Common key tasks by sector key (from SECTOR_OPTIONS values). */
export const SECTOR_TASKS: Record<string, string[]> = {
  manufacturing: [
    "Metal grinding",
    "Spray painting",
    "Solvent cleaning",
    "Welding",
    "Machine operation",
    "Assembly / packing",
  ],
  construction: [
    "Demolition",
    "Concrete cutting",
    "Scaffolding",
    "Site supervision",
    "Groundworks",
    "Roofing",
  ],
  nhs: [
    "Patient care",
    "Phlebotomy",
    "Cleaning / decontamination",
    "Laundry",
    "Facilities maintenance",
    "Administrative duties",
  ],
  transport: [
    "HGV driving",
    "Warehouse picking",
    "Forklift operation",
    "Loading / unloading",
    "Vehicle maintenance",
  ],
  agriculture: [
    "Livestock handling",
    "Pesticide application",
    "Machinery operation",
    "Crop harvesting",
  ],
  education: [
    "Teaching",
    "Laboratory work",
    "Facilities / estates",
    "Catering",
  ],
  local_authority: [
    "Refuse collection",
    "Street cleaning",
    "Parks maintenance",
    "Office / admin",
  ],
  energy: [
    "Plant operation",
    "Confined space work",
    "Electrical maintenance",
    "Offshore / field work",
  ],
  hospitality: [
    "Kitchen / cooking",
    "Cleaning",
    "Front of house",
    "Laundry",
  ],
  other: [],
};

export const WORKFORCE_CHARACTERISTIC_OPTIONS: string[] = [
  "Shift / night workers",
  "Young workers (under 18)",
  "Older workers",
  "Pregnant / new mothers",
  "Workers with disabilities or long-term conditions",
  "Temporary / agency workers",
  "Lone workers",
  "Non-English speaking workers",
  "New starters / high turnover",
];

export const HAZARD_PHRASE_OPTIONS: string[] = [
  "H317 — May cause an allergic skin reaction",
  "H334 — May cause allergy or asthma symptoms or breathing difficulties if inhaled",
  "H350 — May cause cancer",
  "H372 — Causes damage to organs through prolonged or repeated exposure",
  "Noise — Exposure at or above lower exposure action value",
  "Hand-arm vibration — Exposure above EAV",
  "Whole-body vibration",
  "Wet work / skin irritants",
  "Ionising radiation",
  "Biological agents (COSHH / Bio Agents)",
];

export const HEALTH_EFFECT_OPTIONS: string[] = [
  "Occupational asthma / respiratory sensitisation",
  "Noise-induced hearing loss (NIHL)",
  "Hand-arm vibration syndrome (HAVS)",
  "Contact dermatitis",
  "Chronic obstructive pulmonary disease (COPD)",
  "Musculoskeletal disorders",
  "Work-related stress",
  "Lead / heavy metal toxicity",
  "Infectious disease",
];

export const CONTROL_MEASURE_OPTIONS: string[] = [
  "Elimination / substitution",
  "Local exhaust ventilation (LEV)",
  "Respiratory protective equipment (RPE)",
  "Hearing protection",
  "Gloves / PPE",
  "Job rotation / exposure time limits",
  "Training and information",
  "Health surveillance in place",
  "Workplace monitoring / air sampling",
];

export const EXPOSURE_LEVEL_DEFINITIONS: Record<ExposureLevel, string> = {
  negligible: "Exposure unlikely to cause harm under normal conditions",
  low: "Well below relevant WEL/action values or equivalent",
  moderate: "Approaching or intermittently near action values",
  high: "At or above action values / WEL for significant periods",
  very_high: "Well above WEL/action values or uncontrolled peaks",
};

export const EXPOSURE_FREQUENCY_DEFINITIONS: Record<ExposureFrequency, string> = {
  rare: "Less than monthly",
  occasional: "Monthly to weekly",
  frequent: "Several times per week",
  continuous: "Daily / throughout the shift",
};

/** WEL suggestions keyed by lowercase substance/agent substring or category. */
const WEL_BY_AGENT: Record<string, string> = {
  isocyanate: "20 µg/m³ NCO (8-hr TWA)",
  isocyanates: "20 µg/m³ NCO (8-hr TWA)",
  silica: "0.1 mg/m³ respirable crystalline silica (8-hr TWA)",
  asbestos: "0.1 fibres/cm³ (4-hr TWA) — refer to Control of Asbestos Regulations",
  lead: "0.15 mg/m³ (8-hr TWA)",
  noise: "Lower EAV 80 dB(A); Upper EAV 85 dB(A); Limit 87 dB(A)",
  "hand-arm vibration": "EAV 2.5 m/s² A(8); ELV 5 m/s² A(8)",
  havs: "EAV 2.5 m/s² A(8); ELV 5 m/s² A(8)",
  welding: "Refer to EH40 for specific fume constituents",
  "wood dust": "5 mg/m³ inhalable (hardwoods — check EH40)",
};

const HEALTH_EFFECTS_BY_CATEGORY: Partial<Record<HazardCategory, string[]>> = {
  noise: ["Noise-induced hearing loss (NIHL)"],
  vibration: ["Hand-arm vibration syndrome (HAVS)"],
  chemical: ["Occupational asthma / respiratory sensitisation", "Contact dermatitis"],
  dust: ["Chronic obstructive pulmonary disease (COPD)", "Occupational asthma / respiratory sensitisation"],
  skin: ["Contact dermatitis"],
  biological: ["Infectious disease"],
  psychosocial: ["Work-related stress"],
  ergonomic: ["Musculoskeletal disorders"],
};

export function tasksForSector(sectorKey: string): string[] {
  return SECTOR_TASKS[sectorKey] ?? [];
}

export function joinSelections(selected: string[], other: string): string {
  const parts = [...selected.filter(Boolean), other.trim()].filter(Boolean);
  return parts.join("; ");
}

export function splitSelections(
  value: string | undefined | null,
  knownOptions: string[]
): { selected: string[]; other: string } {
  if (!value?.trim()) return { selected: [], other: "" };
  const parts = value.split(";").map((p) => p.trim()).filter(Boolean);
  const known = new Set(knownOptions);
  const selected: string[] = [];
  const otherParts: string[] = [];
  for (const p of parts) {
    if (known.has(p)) selected.push(p);
    else otherParts.push(p);
  }
  return { selected, other: otherParts.join("; ") };
}

export function suggestWel(
  substanceOrAgent: string | undefined | null,
  category?: HazardCategory
): string | undefined {
  const agent = (substanceOrAgent ?? "").toLowerCase().trim();
  if (agent) {
    for (const [key, wel] of Object.entries(WEL_BY_AGENT)) {
      if (agent.includes(key) || key.includes(agent)) return wel;
    }
  }
  if (category && WEL_BY_AGENT[category]) return WEL_BY_AGENT[category];
  return undefined;
}

export function suggestHealthEffects(
  category: HazardCategory,
  substanceOrAgent?: string | null
): string {
  const fromCategory = HEALTH_EFFECTS_BY_CATEGORY[category] ?? [];
  const agent = (substanceOrAgent ?? "").toLowerCase();
  const extras: string[] = [];
  if (agent.includes("isocyanate")) {
    extras.push("Occupational asthma / respiratory sensitisation");
  }
  if (agent.includes("noise")) {
    extras.push("Noise-induced hearing loss (NIHL)");
  }
  const combined = [...new Set([...fromCategory, ...extras])];
  return combined.join("; ");
}

export function exposureLevelDefinition(level: ExposureLevel): string {
  return EXPOSURE_LEVEL_DEFINITIONS[level];
}

export function exposureFrequencyDefinition(freq: ExposureFrequency): string {
  return EXPOSURE_FREQUENCY_DEFINITIONS[freq];
}
