/**
 * Curated authoritative resource links for human-in-the-loop review.
 * Filtered by hazard category where relevant.
 */

import type { HazardCategory } from "@/lib/types";

export interface ResourceLink {
  title: string;
  url: string;
  description: string;
  /** If set, only show when one of these categories is present (empty = always). */
  categories?: HazardCategory[];
}

export const CURATED_RESOURCE_LINKS: ResourceLink[] = [
  {
    title: "HSE — Steps needed to manage risk",
    url: "https://www.hse.gov.uk/simple-health-safety/risk/steps-needed-to-manage-risk.htm",
    description: "Nationally recognised five steps to risk assessment.",
  },
  {
    title: "HSE — Health surveillance",
    url: "https://www.hse.gov.uk/health-surveillance/",
    description: "When health surveillance is required and levels of surveillance.",
  },
  {
    title: "HSE — Managing risk using PPE",
    url: "https://www.hse.gov.uk/ppe/",
    description: "Hierarchy of controls; PPE as last line of defence.",
  },
  {
    title: "SEQOHS standards",
    url: "https://www.seqohs.org/",
    description: "Safe Effective Quality Occupational Health Service (e.g. domains 3.2, 5.2).",
  },
  {
    title: "ARTP — Training & Development",
    url: "https://www.artp.org.uk/Training-and-Development",
    description: "Respiratory / spirometry training guidance.",
    categories: ["chemical", "dust", "biological"],
  },
  {
    title: "British Society of Audiology",
    url: "https://www.thebsa.org.uk/",
    description: "Audiometry training and practice guidance.",
    categories: ["noise"],
  },
  {
    title: "HSE — Noise at work",
    url: "https://www.hse.gov.uk/noise/",
    description: "Control of Noise at Work Regulations guidance.",
    categories: ["noise"],
  },
  {
    title: "HSE — Skin at work / wet work",
    url: "https://www.hse.gov.uk/skin/",
    description: "Dermatitis and wet-work health surveillance.",
    categories: ["skin", "chemical"],
  },
  {
    title: "HSE — COSHH",
    url: "https://www.hse.gov.uk/coshh/",
    description: "Control of Substances Hazardous to Health.",
    categories: ["chemical", "dust", "biological"],
  },
];

export function resourcesForHazards(
  categories: HazardCategory[],
  sourcesCited: string[] = []
): ResourceLink[] {
  const cats = new Set(categories);
  const curated = CURATED_RESOURCE_LINKS.filter(
    (r) => !r.categories?.length || r.categories.some((c) => cats.has(c))
  );
  const cited: ResourceLink[] = [];
  for (const src of sourcesCited) {
    const urlMatch = src.match(/https?:\/\/[^\s)]+/i);
    if (!urlMatch) continue;
    const url = urlMatch[0];
    if (curated.some((c) => c.url === url) || cited.some((c) => c.url === url)) continue;
    cited.push({
      title: src.replace(url, "").replace(/[-–—:]\s*$/, "").trim() || url,
      url,
      description: "Cited in generated output",
    });
  }
  return [...curated, ...cited];
}
