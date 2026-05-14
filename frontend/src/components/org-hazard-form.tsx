"use client";

import { useState } from "react";
import { Plus, Trash2, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";
import { Checkbox } from "@/components/ui/checkbox";
import type {
  DeliveryModel,
  ExposureDuration,
  ExposureFrequency,
  ExposureLevel,
  HazardCategory,
  HazardProfile,
  OrganisationProfile,
  RiskAssessmentConfirmation,
} from "@/lib/types";

const HAZARD_CATEGORIES: { value: HazardCategory; label: string }[] = [
  { value: "chemical", label: "Chemical" },
  { value: "biological", label: "Biological" },
  { value: "physical", label: "Physical" },
  { value: "ergonomic", label: "Ergonomic" },
  { value: "psychosocial", label: "Psychosocial" },
  { value: "noise", label: "Noise" },
  { value: "vibration", label: "Vibration" },
  { value: "radiation", label: "Radiation" },
  { value: "dust", label: "Dust" },
  { value: "skin", label: "Skin (wet work)" },
];

const EXPOSURE_LEVELS: { value: ExposureLevel; label: string }[] = [
  { value: "negligible", label: "Negligible" },
  { value: "low", label: "Low" },
  { value: "moderate", label: "Moderate" },
  { value: "high", label: "High" },
  { value: "very_high", label: "Very High" },
];

const EXPOSURE_FREQUENCIES: { value: ExposureFrequency; label: string }[] = [
  { value: "rare", label: "Rare" },
  { value: "occasional", label: "Occasional" },
  { value: "frequent", label: "Frequent" },
  { value: "continuous", label: "Continuous" },
];

const EXPOSURE_DURATIONS: { value: ExposureDuration; label: string }[] = [
  { value: "brief", label: "Brief (minutes)" },
  { value: "short", label: "Short (up to 1hr)" },
  { value: "medium", label: "Medium (1–4hrs)" },
  { value: "long", label: "Long (4–8hrs)" },
  { value: "extended", label: "Extended (>8hrs)" },
];

const DELIVERY_MODELS: { value: DeliveryModel; label: string }[] = [
  { value: "ohp_led", label: "OHP-led" },
  { value: "ohn_led", label: "OHN-led" },
  { value: "technician", label: "Technician-delivered" },
  { value: "mixed", label: "Mixed" },
];

function emptyHazard(): HazardProfile {
  return {
    category: "chemical",
    hazard_phrase: "",
    substance_or_agent: "",
    exposure_level: "moderate",
    exposure_frequency: "frequent",
    exposure_duration: "medium",
    workplace_exposure_limit: "",
    potential_health_effects: "",
    existing_controls: "",
    notes: "",
  };
}

interface OrgHazardFormProps {
  submitLabel: string;
  loading: boolean;
  showAdditionalContext?: boolean;
  showRiskAssessment?: boolean;
  onSubmit: (
    org: OrganisationProfile,
    hazards: HazardProfile[],
    additionalContext?: string,
    riskAssessment?: RiskAssessmentConfirmation
  ) => void;
}

export function OrgHazardForm({
  submitLabel,
  loading,
  showAdditionalContext = false,
  showRiskAssessment = false,
  onSubmit,
}: OrgHazardFormProps) {
  const [org, setOrg] = useState<OrganisationProfile>({
    name: "",
    sector: "",
    tasks: [],
    workforce_size: undefined,
    workforce_characteristics: "",
    multi_site: false,
    site_count: 1,
    delivery_model: "mixed",
    existing_surveillance: "",
    risk_assessment_confirmed: false,
    workers_consulted: false,
  });
  const [tasksText, setTasksText] = useState("");
  const [hazards, setHazards] = useState<HazardProfile[]>([emptyHazard()]);
  const [additionalContext, setAdditionalContext] = useState("");
  const [riskAssessment, setRiskAssessment] = useState<RiskAssessmentConfirmation>({
    risk_assessment_completed: false,
    workers_consulted: false,
    risk_assessment_date: "",
    assessor_name: "",
    additional_notes: "",
  });

  const updateHazard = (idx: number, patch: Partial<HazardProfile>) => {
    setHazards((prev) =>
      prev.map((h, i) => (i === idx ? { ...h, ...patch } : h))
    );
  };

  const removeHazard = (idx: number) => {
    setHazards((prev) => prev.filter((_, i) => i !== idx));
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const finalOrg: OrganisationProfile = {
      ...org,
      tasks: tasksText
        .split(",")
        .map((t) => t.trim())
        .filter(Boolean),
    };
    const cleanedHazards = hazards.filter((h) => h.hazard_phrase.trim());
    if (!finalOrg.name || !finalOrg.sector || cleanedHazards.length === 0) return;
    onSubmit(
      finalOrg,
      cleanedHazards,
      additionalContext || undefined,
      showRiskAssessment ? riskAssessment : undefined
    );
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle className="text-base">
            PLAN — Organisation &amp; Risk Profile
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="org-name">Organisation Name *</Label>
              <Input
                id="org-name"
                value={org.name}
                onChange={(e) => setOrg({ ...org, name: e.target.value })}
                placeholder="e.g. Acme Manufacturing Ltd"
                required
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="sector">Sector *</Label>
              <Input
                id="sector"
                value={org.sector}
                onChange={(e) => setOrg({ ...org, sector: e.target.value })}
                placeholder="e.g. manufacturing, NHS, construction"
                required
              />
            </div>
          </div>
          <div className="space-y-2">
            <Label htmlFor="tasks">Key Tasks (comma-separated)</Label>
            <Input
              id="tasks"
              value={tasksText}
              onChange={(e) => setTasksText(e.target.value)}
              placeholder="e.g. metal grinding, spray painting, solvent cleaning"
            />
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <div className="space-y-2">
              <Label htmlFor="workforce-size">Workforce Size</Label>
              <Input
                id="workforce-size"
                type="number"
                min={1}
                value={org.workforce_size ?? ""}
                onChange={(e) =>
                  setOrg({
                    ...org,
                    workforce_size: e.target.value
                      ? Number(e.target.value)
                      : undefined,
                  })
                }
                placeholder="e.g. 250"
              />
            </div>
            <div className="space-y-2">
              <Label>Delivery Model</Label>
              <Select
                value={org.delivery_model}
                onValueChange={(v) =>
                  setOrg({ ...org, delivery_model: v as DeliveryModel })
                }
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {DELIVERY_MODELS.map((d) => (
                    <SelectItem key={d.value} value={d.value}>
                      {d.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-2">
              <Label htmlFor="site-count">Number of Sites</Label>
              <Input
                id="site-count"
                type="number"
                min={1}
                value={org.site_count}
                onChange={(e) =>
                  setOrg({
                    ...org,
                    site_count: Number(e.target.value) || 1,
                    multi_site: Number(e.target.value) > 1,
                  })
                }
              />
            </div>
          </div>
          <div className="space-y-2">
            <Label htmlFor="workforce-chars">
              Workforce Characteristics (incl. vulnerability)
            </Label>
            <Input
              id="workforce-chars"
              value={org.workforce_characteristics ?? ""}
              onChange={(e) =>
                setOrg({ ...org, workforce_characteristics: e.target.value })
              }
              placeholder="e.g. shift workers, mixed age, includes vulnerable groups"
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="existing-surv">Existing Surveillance</Label>
            <Textarea
              id="existing-surv"
              value={org.existing_surveillance ?? ""}
              onChange={(e) =>
                setOrg({ ...org, existing_surveillance: e.target.value })
              }
              placeholder="Describe current health surveillance arrangements"
              rows={2}
            />
          </div>
          <Separator />
          <div className="space-y-3">
            <p className="text-sm font-medium">PLAN Confirmations</p>
            <div className="flex items-center gap-2">
              <Checkbox
                id="risk-assessment"
                checked={org.risk_assessment_confirmed}
                onCheckedChange={(v) =>
                  setOrg({ ...org, risk_assessment_confirmed: v === true })
                }
              />
              <Label htmlFor="risk-assessment" className="text-sm font-normal">
                A suitable and sufficient risk assessment has been undertaken
                (Management Regulations)
              </Label>
            </div>
            <div className="flex items-center gap-2">
              <Checkbox
                id="workers-consulted"
                checked={org.workers_consulted}
                onCheckedChange={(v) =>
                  setOrg({ ...org, workers_consulted: v === true })
                }
              />
              <Label htmlFor="workers-consulted" className="text-sm font-normal">
                Workers have been consulted on perceived hazards and practicality
                of controls (HSWA duty)
              </Label>
            </div>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="flex flex-row items-center justify-between">
          <CardTitle className="text-base">Hazard Profiles *</CardTitle>
          <Button
            type="button"
            variant="outline"
            size="sm"
            onClick={() => setHazards([...hazards, emptyHazard()])}
          >
            <Plus className="mr-1 h-4 w-4" /> Add Hazard
          </Button>
        </CardHeader>
        <CardContent className="space-y-4">
          {hazards.map((hazard, idx) => (
            <div key={idx}>
              {idx > 0 && <Separator className="mb-4" />}
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium text-muted-foreground">
                    Hazard {idx + 1}
                  </span>
                  {hazards.length > 1 && (
                    <Button
                      type="button"
                      variant="ghost"
                      size="sm"
                      onClick={() => removeHazard(idx)}
                    >
                      <Trash2 className="h-4 w-4 text-destructive" />
                    </Button>
                  )}
                </div>
                <div className="grid grid-cols-1 sm:grid-cols-4 gap-3">
                  <div className="space-y-1">
                    <Label>Category</Label>
                    <Select
                      value={hazard.category}
                      onValueChange={(v) =>
                        updateHazard(idx, {
                          category: v as HazardCategory,
                        })
                      }
                    >
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        {HAZARD_CATEGORIES.map((c) => (
                          <SelectItem key={c.value} value={c.value}>
                            {c.label}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="space-y-1">
                    <Label>Exposure Level</Label>
                    <Select
                      value={hazard.exposure_level}
                      onValueChange={(v) =>
                        updateHazard(idx, {
                          exposure_level: v as ExposureLevel,
                        })
                      }
                    >
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        {EXPOSURE_LEVELS.map((l) => (
                          <SelectItem key={l.value} value={l.value}>
                            {l.label}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="space-y-1">
                    <Label>Frequency</Label>
                    <Select
                      value={hazard.exposure_frequency}
                      onValueChange={(v) =>
                        updateHazard(idx, {
                          exposure_frequency: v as ExposureFrequency,
                        })
                      }
                    >
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        {EXPOSURE_FREQUENCIES.map((f) => (
                          <SelectItem key={f.value} value={f.value}>
                            {f.label}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="space-y-1">
                    <Label>Duration</Label>
                    <Select
                      value={hazard.exposure_duration}
                      onValueChange={(v) =>
                        updateHazard(idx, {
                          exposure_duration: v as ExposureDuration,
                        })
                      }
                    >
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        {EXPOSURE_DURATIONS.map((d) => (
                          <SelectItem key={d.value} value={d.value}>
                            {d.label}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                </div>
                <div className="space-y-1">
                  <Label>Hazard Phrase *</Label>
                  <Input
                    value={hazard.hazard_phrase}
                    onChange={(e) =>
                      updateHazard(idx, { hazard_phrase: e.target.value })
                    }
                    placeholder="e.g. H334 — May cause allergy or asthma symptoms if inhaled"
                    required
                  />
                </div>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                  <div className="space-y-1">
                    <Label>Substance / Agent</Label>
                    <Input
                      value={hazard.substance_or_agent ?? ""}
                      onChange={(e) =>
                        updateHazard(idx, {
                          substance_or_agent: e.target.value,
                        })
                      }
                      placeholder="e.g. isocyanates"
                    />
                  </div>
                  <div className="space-y-1">
                    <Label>Workplace Exposure Limit</Label>
                    <Input
                      value={hazard.workplace_exposure_limit ?? ""}
                      onChange={(e) =>
                        updateHazard(idx, {
                          workplace_exposure_limit: e.target.value,
                        })
                      }
                      placeholder="e.g. 20 µg/m³ NCO (8-hr TWA)"
                    />
                  </div>
                </div>
                <div className="space-y-1">
                  <Label>Potential Health Effects</Label>
                  <Input
                    value={hazard.potential_health_effects ?? ""}
                    onChange={(e) =>
                      updateHazard(idx, {
                        potential_health_effects: e.target.value,
                      })
                    }
                    placeholder="e.g. Occupational asthma, sensitisation"
                  />
                </div>
                <div className="space-y-1">
                  <Label>Existing Control Measures</Label>
                  <Input
                    value={hazard.existing_controls ?? ""}
                    onChange={(e) =>
                      updateHazard(idx, {
                        existing_controls: e.target.value,
                      })
                    }
                    placeholder="e.g. LEV installed, RPE provided, limited compliance"
                  />
                </div>
              </div>
            </div>
          ))}
        </CardContent>
      </Card>

      {showAdditionalContext && (
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Additional Context</CardTitle>
          </CardHeader>
          <CardContent>
            <Textarea
              value={additionalContext}
              onChange={(e) => setAdditionalContext(e.target.value)}
              placeholder="Any additional context for the workflow generation..."
              rows={3}
            />
          </CardContent>
        </Card>
      )}

      {showRiskAssessment && (
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Risk Assessment Confirmation</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center gap-2">
              <Checkbox
                id="ra-completed"
                checked={riskAssessment.risk_assessment_completed}
                onCheckedChange={(v) =>
                  setRiskAssessment({ ...riskAssessment, risk_assessment_completed: v === true })
                }
                required
              />
              <Label htmlFor="ra-completed" className="text-sm font-normal">
                Risk assessment has been completed
              </Label>
            </div>
            <div className="flex items-center gap-2">
              <Checkbox
                id="ra-workers"
                checked={riskAssessment.workers_consulted}
                onCheckedChange={(v) =>
                  setRiskAssessment({ ...riskAssessment, workers_consulted: v === true })
                }
                required
              />
              <Label htmlFor="ra-workers" className="text-sm font-normal">
                Workers have been consulted
              </Label>
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="ra-date">Risk Assessment Date</Label>
                <Input
                  id="ra-date"
                  type="date"
                  value={riskAssessment.risk_assessment_date ?? ""}
                  onChange={(e) =>
                    setRiskAssessment({ ...riskAssessment, risk_assessment_date: e.target.value })
                  }
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="ra-assessor">Assessor Name</Label>
                <Input
                  id="ra-assessor"
                  value={riskAssessment.assessor_name ?? ""}
                  onChange={(e) =>
                    setRiskAssessment({ ...riskAssessment, assessor_name: e.target.value })
                  }
                  placeholder="e.g. Dr. Jane Smith"
                />
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      <Button type="submit" disabled={loading} className="w-full sm:w-auto">
        {loading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
        {submitLabel}
      </Button>
    </form>
  );
}
