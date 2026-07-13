"use client";

import { useEffect, useRef, useState } from "react";
import { Plus, Trash2, Loader2, Save } from "lucide-react";
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
import {
  CONTROL_MEASURE_OPTIONS,
  HAZARD_PHRASE_OPTIONS,
  HEALTH_EFFECT_OPTIONS,
  SECTOR_OPTIONS,
  WORKFORCE_CHARACTERISTIC_OPTIONS,
  exposureFrequencyDefinition,
  exposureLevelDefinition,
  joinSelections,
  splitSelections,
  suggestHealthEffects,
  suggestWel,
  tasksForSector,
} from "@/lib/form-options";
import {
  deleteNamedDraft,
  listNamedDrafts,
  loadLiveDraft,
  loadNamedDraft,
  saveLiveDraft,
  saveNamedDraft,
  type NamedDraft,
} from "@/lib/form-draft";

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
  { value: "none", label: "No OH service currently in place" },
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

function defaultOrg(): OrganisationProfile {
  return {
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
  };
}

function defaultRiskAssessment(): RiskAssessmentConfirmation {
  return {
    risk_assessment_completed: false,
    workers_consulted: false,
    risk_assessment_date: "",
    assessor_name: "",
    additional_notes: "",
  };
}

function MultiCheck({
  options,
  selected,
  onChange,
  idPrefix,
}: {
  options: string[];
  selected: string[];
  onChange: (next: string[]) => void;
  idPrefix: string;
}) {
  const toggle = (opt: string, checked: boolean) => {
    if (checked) onChange([...selected, opt]);
    else onChange(selected.filter((s) => s !== opt));
  };
  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
      {options.map((opt) => {
        const id = `${idPrefix}-${opt.slice(0, 24)}`;
        return (
          <div key={opt} className="flex items-start gap-2">
            <Checkbox
              id={id}
              checked={selected.includes(opt)}
              onCheckedChange={(v) => toggle(opt, v === true)}
            />
            <Label htmlFor={id} className="text-sm font-normal leading-snug">
              {opt}
            </Label>
          </div>
        );
      })}
    </div>
  );
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

type FormUiState = {
  org: OrganisationProfile;
  sectorKey: string;
  sectorOther: string;
  selectedTasks: string[];
  tasksOther: string;
  workforceSelected: string[];
  workforceOther: string;
  hazards: HazardProfile[];
  phraseSelected: string[][];
  phraseOther: string[];
  effectsSelected: string[][];
  effectsOther: string[];
  controlsSelected: string[][];
  controlsOther: string[];
  additionalContext: string;
  riskAssessment: RiskAssessmentConfirmation;
};

function emptyUiState(): FormUiState {
  return {
    org: defaultOrg(),
    sectorKey: "",
    sectorOther: "",
    selectedTasks: [],
    tasksOther: "",
    workforceSelected: [],
    workforceOther: "",
    hazards: [emptyHazard()],
    phraseSelected: [[]],
    phraseOther: [""],
    effectsSelected: [[]],
    effectsOther: [""],
    controlsSelected: [[]],
    controlsOther: [""],
    additionalContext: "",
    riskAssessment: defaultRiskAssessment(),
  };
}

function uiStateFromPayload(
  nextOrg: OrganisationProfile,
  nextHazards: HazardProfile[],
  tasksText: string,
  ctx: string,
  ra: RiskAssessmentConfirmation
): FormUiState {
  const matchedSector = SECTOR_OPTIONS.find(
    (s) =>
      s.label.toLowerCase() === nextOrg.sector.toLowerCase() ||
      s.value === nextOrg.sector.toLowerCase()
  );
  let sectorKey = "";
  let sectorOther = "";
  if (matchedSector && matchedSector.value !== "other") {
    sectorKey = matchedSector.value;
  } else if (nextOrg.sector) {
    sectorKey = "other";
    sectorOther = nextOrg.sector;
  }
  const taskParts = (tasksText || nextOrg.tasks.join("; "))
    .split(/[;,]/)
    .map((t) => t.trim())
    .filter(Boolean);
  const knownTasks = new Set(tasksForSector(matchedSector?.value ?? "other"));
  const hz = nextHazards.length ? nextHazards : [emptyHazard()];
  const wf = splitSelections(nextOrg.workforce_characteristics, WORKFORCE_CHARACTERISTIC_OPTIONS);
  return {
    org: nextOrg,
    sectorKey,
    sectorOther,
    selectedTasks: taskParts.filter((t) => knownTasks.has(t)),
    tasksOther: taskParts.filter((t) => !knownTasks.has(t)).join("; "),
    workforceSelected: wf.selected,
    workforceOther: wf.other,
    hazards: hz,
    phraseSelected: hz.map((h) => splitSelections(h.hazard_phrase, HAZARD_PHRASE_OPTIONS).selected),
    phraseOther: hz.map((h) => splitSelections(h.hazard_phrase, HAZARD_PHRASE_OPTIONS).other),
    effectsSelected: hz.map(
      (h) => splitSelections(h.potential_health_effects, HEALTH_EFFECT_OPTIONS).selected
    ),
    effectsOther: hz.map(
      (h) => splitSelections(h.potential_health_effects, HEALTH_EFFECT_OPTIONS).other
    ),
    controlsSelected: hz.map(
      (h) => splitSelections(h.existing_controls, CONTROL_MEASURE_OPTIONS).selected
    ),
    controlsOther: hz.map(
      (h) => splitSelections(h.existing_controls, CONTROL_MEASURE_OPTIONS).other
    ),
    additionalContext: ctx,
    riskAssessment: ra,
  };
}

function initialUiState(): FormUiState {
  if (typeof window === "undefined") return emptyUiState();
  const draft = loadLiveDraft();
  if (!draft) return emptyUiState();
  return uiStateFromPayload(
    draft.org,
    draft.hazards,
    draft.tasksText,
    draft.additionalContext,
    draft.riskAssessment
  );
}

export function OrgHazardForm({
  submitLabel,
  loading,
  showAdditionalContext = false,
  showRiskAssessment = false,
  onSubmit,
}: OrgHazardFormProps) {
  const [ui, setUi] = useState<FormUiState>(initialUiState);
  const {
    org,
    sectorKey,
    sectorOther,
    selectedTasks,
    tasksOther,
    workforceSelected,
    workforceOther,
    hazards,
    phraseSelected,
    phraseOther,
    effectsSelected,
    effectsOther,
    controlsSelected,
    controlsOther,
    additionalContext,
    riskAssessment,
  } = ui;

  const setOrg = (next: OrganisationProfile | ((prev: OrganisationProfile) => OrganisationProfile)) =>
    setUi((s) => ({ ...s, org: typeof next === "function" ? next(s.org) : next }));
  const setSectorOther = (sectorOther: string) => setUi((s) => ({ ...s, sectorOther }));
  const setSelectedTasks = (selectedTasks: string[]) => setUi((s) => ({ ...s, selectedTasks }));
  const setTasksOther = (tasksOther: string) => setUi((s) => ({ ...s, tasksOther }));
  const setWorkforceSelected = (workforceSelected: string[]) =>
    setUi((s) => ({ ...s, workforceSelected }));
  const setWorkforceOther = (workforceOther: string) => setUi((s) => ({ ...s, workforceOther }));
  const setHazards = (next: HazardProfile[] | ((prev: HazardProfile[]) => HazardProfile[])) =>
    setUi((s) => ({ ...s, hazards: typeof next === "function" ? next(s.hazards) : next }));
  const setPhraseSelected = (next: string[][] | ((prev: string[][]) => string[][])) =>
    setUi((s) => ({
      ...s,
      phraseSelected: typeof next === "function" ? next(s.phraseSelected) : next,
    }));
  const setPhraseOther = (next: string[] | ((prev: string[]) => string[])) =>
    setUi((s) => ({
      ...s,
      phraseOther: typeof next === "function" ? next(s.phraseOther) : next,
    }));
  const setEffectsSelected = (next: string[][] | ((prev: string[][]) => string[][])) =>
    setUi((s) => ({
      ...s,
      effectsSelected: typeof next === "function" ? next(s.effectsSelected) : next,
    }));
  const setEffectsOther = (next: string[] | ((prev: string[]) => string[])) =>
    setUi((s) => ({
      ...s,
      effectsOther: typeof next === "function" ? next(s.effectsOther) : next,
    }));
  const setControlsSelected = (next: string[][] | ((prev: string[][]) => string[][])) =>
    setUi((s) => ({
      ...s,
      controlsSelected: typeof next === "function" ? next(s.controlsSelected) : next,
    }));
  const setControlsOther = (next: string[] | ((prev: string[]) => string[])) =>
    setUi((s) => ({
      ...s,
      controlsOther: typeof next === "function" ? next(s.controlsOther) : next,
    }));
  const setAdditionalContext = (additionalContext: string) =>
    setUi((s) => ({ ...s, additionalContext }));
  const setRiskAssessment = (
    next:
      | RiskAssessmentConfirmation
      | ((prev: RiskAssessmentConfirmation) => RiskAssessmentConfirmation)
  ) =>
    setUi((s) => ({
      ...s,
      riskAssessment: typeof next === "function" ? next(s.riskAssessment) : next,
    }));

  const [namedDrafts, setNamedDrafts] = useState<NamedDraft[]>(() =>
    typeof window === "undefined" ? [] : listNamedDrafts()
  );
  const [draftName, setDraftName] = useState("");
  const skipFirstPersist = useRef(true);

  const refreshNamedDrafts = () => setNamedDrafts(listNamedDrafts());

  useEffect(() => {
    if (skipFirstPersist.current) {
      skipFirstPersist.current = false;
      return;
    }
    const tasksText = joinSelections(selectedTasks, tasksOther);
    const t = window.setTimeout(() => {
      saveLiveDraft({
        org: {
          ...org,
          sector: resolveSector(),
          tasks: tasksText.split(";").map((x) => x.trim()).filter(Boolean),
          workforce_characteristics: joinSelections(workforceSelected, workforceOther),
        },
        hazards: hazards.map((h, i) => enrichHazard(h, i)),
        tasksText,
        additionalContext,
        riskAssessment,
      });
    }, 400);
    return () => window.clearTimeout(t);
    // Intentionally persist whenever form UI fields change
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [ui]);

  function resolveSector(): string {
    if (sectorKey === "other") return sectorOther.trim() || "other";
    const opt = SECTOR_OPTIONS.find((s) => s.value === sectorKey);
    return opt?.label ?? (sectorOther.trim() || sectorKey);
  }

  function enrichHazard(h: HazardProfile, i: number): HazardProfile {
    return {
      ...h,
      hazard_phrase: joinSelections(phraseSelected[i] ?? [], phraseOther[i] ?? "") || undefined,
      potential_health_effects:
        joinSelections(effectsSelected[i] ?? [], effectsOther[i] ?? "") || undefined,
      existing_controls:
        joinSelections(controlsSelected[i] ?? [], controlsOther[i] ?? "") || undefined,
    };
  }

  function applyPayload(
    nextOrg: OrganisationProfile,
    nextHazards: HazardProfile[],
    tasksText: string,
    ctx: string,
    ra: RiskAssessmentConfirmation
  ) {
    setUi(uiStateFromPayload(nextOrg, nextHazards, tasksText, ctx, ra));
  }

  const updateHazard = (idx: number, patch: Partial<HazardProfile>) => {
    setHazards((prev) => prev.map((h, i) => (i === idx ? { ...h, ...patch } : h)));
  };

  const addHazard = () => {
    setUi((s) => ({
      ...s,
      hazards: [...s.hazards, emptyHazard()],
      phraseSelected: [...s.phraseSelected, []],
      phraseOther: [...s.phraseOther, ""],
      effectsSelected: [...s.effectsSelected, []],
      effectsOther: [...s.effectsOther, ""],
      controlsSelected: [...s.controlsSelected, []],
      controlsOther: [...s.controlsOther, ""],
    }));
  };

  const removeHazard = (idx: number) => {
    setUi((s) => ({
      ...s,
      hazards: s.hazards.filter((_, i) => i !== idx),
      phraseSelected: s.phraseSelected.filter((_, i) => i !== idx),
      phraseOther: s.phraseOther.filter((_, i) => i !== idx),
      effectsSelected: s.effectsSelected.filter((_, i) => i !== idx),
      effectsOther: s.effectsOther.filter((_, i) => i !== idx),
      controlsSelected: s.controlsSelected.filter((_, i) => i !== idx),
      controlsOther: s.controlsOther.filter((_, i) => i !== idx),
    }));
  };

  const applyAgentSuggestions = (idx: number, agent: string, category: HazardCategory) => {
    const wel = suggestWel(agent, category);
    const effects = suggestHealthEffects(category, agent);
    updateHazard(idx, {
      substance_or_agent: agent,
      ...(wel && !hazards[idx].workplace_exposure_limit
        ? { workplace_exposure_limit: wel }
        : {}),
    });
    if (effects && !(effectsSelected[idx]?.length || effectsOther[idx]?.trim())) {
      const split = splitSelections(effects, HEALTH_EFFECT_OPTIONS);
      setEffectsSelected((prev) => prev.map((row, i) => (i === idx ? split.selected : row)));
      setEffectsOther((prev) => prev.map((row, i) => (i === idx ? split.other : row)));
    }
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const sector = resolveSector();
    const tasks = joinSelections(selectedTasks, tasksOther)
      .split(";")
      .map((t) => t.trim())
      .filter(Boolean);
    const finalOrg: OrganisationProfile = {
      ...org,
      sector,
      tasks,
      workforce_characteristics: joinSelections(workforceSelected, workforceOther) || undefined,
    };
    if (showRiskAssessment) {
      finalOrg.risk_assessment_confirmed = riskAssessment.risk_assessment_completed;
      finalOrg.workers_consulted = riskAssessment.workers_consulted;
    }
    const cleanedHazards = hazards
      .map((h, i) => enrichHazard(h, i))
      .filter(
        (h) =>
          (h.hazard_phrase && h.hazard_phrase.trim()) ||
          (h.substance_or_agent && h.substance_or_agent.trim())
      );
    if (!finalOrg.name || !finalOrg.sector || cleanedHazards.length === 0) return;
    onSubmit(
      finalOrg,
      cleanedHazards,
      additionalContext || undefined,
      showRiskAssessment ? riskAssessment : undefined
    );
  };

  const handleSaveNamed = () => {
    const tasksText = joinSelections(selectedTasks, tasksOther);
    saveNamedDraft(draftName || org.name || "Untitled", {
      org: {
        ...org,
        sector: resolveSector(),
        tasks: tasksText.split(";").map((x) => x.trim()).filter(Boolean),
        workforce_characteristics: joinSelections(workforceSelected, workforceOther),
      },
      hazards: hazards.map((h, i) => enrichHazard(h, i)),
      tasksText,
      additionalContext,
      riskAssessment,
    });
    setDraftName("");
    refreshNamedDrafts();
  };

  const handleLoadNamed = (id: string) => {
    const draft = loadNamedDraft(id);
    if (!draft) return;
    applyPayload(
      draft.payload.org,
      draft.payload.hazards,
      draft.payload.tasksText,
      draft.payload.additionalContext,
      draft.payload.riskAssessment
    );
  };

  const sectorTaskOptions = tasksForSector(sectorKey === "other" ? "other" : sectorKey);

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      <Card>
        <CardHeader className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <CardTitle className="text-base">PLAN — Organisation &amp; Risk Profile</CardTitle>
          <div className="flex flex-wrap items-center gap-2">
            <Input
              className="h-8 w-36 text-sm"
              placeholder="Draft name"
              value={draftName}
              onChange={(e) => setDraftName(e.target.value)}
            />
            <Button type="button" variant="outline" size="sm" onClick={handleSaveNamed}>
              <Save className="mr-1 h-3.5 w-3.5" /> Save draft
            </Button>
            {namedDrafts.length > 0 && (
              <Select onValueChange={(id) => id && handleLoadNamed(id)}>
                <SelectTrigger className="h-8 w-40">
                  <SelectValue placeholder="Load draft" />
                </SelectTrigger>
                <SelectContent>
                  {namedDrafts.map((d) => (
                    <SelectItem key={d.id} value={d.id}>
                      {d.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            )}
            {namedDrafts.length > 0 && (
              <Button
                type="button"
                variant="ghost"
                size="sm"
                onClick={() => {
                  namedDrafts.forEach((d) => deleteNamedDraft(d.id));
                  refreshNamedDrafts();
                }}
              >
                Clear history
              </Button>
            )}
          </div>
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
              <Label>Sector *</Label>
              <Select
                value={sectorKey}
                onValueChange={(v) => {
                  if (!v) return;
                  setUi((s) => ({
                    ...s,
                    sectorKey: v,
                    selectedTasks: [],
                    tasksOther: "",
                  }));
                }}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Select sector" />
                </SelectTrigger>
                <SelectContent>
                  {SECTOR_OPTIONS.map((s) => (
                    <SelectItem key={s.value} value={s.value}>
                      {s.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              {sectorKey === "other" && (
                <Input
                  value={sectorOther}
                  onChange={(e) => setSectorOther(e.target.value)}
                  placeholder="Describe sector"
                  required
                />
              )}
            </div>
          </div>

          <div className="space-y-2">
            <Label>Key Tasks (select all that apply)</Label>
            {sectorTaskOptions.length > 0 ? (
              <MultiCheck
                idPrefix="task"
                options={sectorTaskOptions}
                selected={selectedTasks}
                onChange={setSelectedTasks}
              />
            ) : (
              <p className="text-sm text-muted-foreground">
                Select a sector to see common tasks, or enter tasks below.
              </p>
            )}
            <Input
              value={tasksOther}
              onChange={(e) => setTasksOther(e.target.value)}
              placeholder="Other tasks (semicolon-separated)"
            />
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <div className="space-y-2">
              <Label htmlFor="workforce-size">Number of workers exposed</Label>
              <Input
                id="workforce-size"
                type="number"
                min={1}
                value={org.workforce_size ?? ""}
                onChange={(e) =>
                  setOrg({
                    ...org,
                    workforce_size: e.target.value ? Number(e.target.value) : undefined,
                  })
                }
                placeholder="e.g. 250"
              />
            </div>
            <div className="space-y-2">
              <Label>Model of OH Delivery</Label>
              <Select
                value={org.delivery_model}
                onValueChange={(v) =>
                  v && setOrg({ ...org, delivery_model: v as DeliveryModel })
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
            <Label>Workforce Characteristics (select all that apply)</Label>
            <MultiCheck
              idPrefix="wf"
              options={WORKFORCE_CHARACTERISTIC_OPTIONS}
              selected={workforceSelected}
              onChange={setWorkforceSelected}
            />
            <Input
              value={workforceOther}
              onChange={(e) => setWorkforceOther(e.target.value)}
              placeholder="Other characteristics"
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="existing-surv">Existing Surveillance</Label>
            <Textarea
              id="existing-surv"
              value={org.existing_surveillance ?? ""}
              onChange={(e) => setOrg({ ...org, existing_surveillance: e.target.value })}
              placeholder="Describe current health surveillance arrangements"
              rows={2}
            />
          </div>

          {!showRiskAssessment && (
            <>
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
            </>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="flex flex-row items-center justify-between">
          <CardTitle className="text-base">Hazard Profiles *</CardTitle>
          <Button type="button" variant="outline" size="sm" onClick={addHazard}>
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
                      onValueChange={(v) => {
                        if (!v) return;
                        const cat = v as HazardCategory;
                        updateHazard(idx, { category: cat });
                        applyAgentSuggestions(idx, hazard.substance_or_agent ?? "", cat);
                      }}
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
                        v &&
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
                    <p className="text-xs text-muted-foreground">
                      {exposureLevelDefinition(hazard.exposure_level)}
                    </p>
                  </div>
                  <div className="space-y-1">
                    <Label>Frequency</Label>
                    <Select
                      value={hazard.exposure_frequency}
                      onValueChange={(v) =>
                        v &&
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
                    <p className="text-xs text-muted-foreground">
                      {exposureFrequencyDefinition(hazard.exposure_frequency)}
                    </p>
                  </div>
                  <div className="space-y-1">
                    <Label>Duration</Label>
                    <Select
                      value={hazard.exposure_duration}
                      onValueChange={(v) =>
                        v &&
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
                  <Label>Hazard Phrase (optional — select all that apply)</Label>
                  <MultiCheck
                    idPrefix={`hp-${idx}`}
                    options={HAZARD_PHRASE_OPTIONS}
                    selected={phraseSelected[idx] ?? []}
                    onChange={(next) =>
                      setPhraseSelected((prev) =>
                        prev.map((row, i) => (i === idx ? next : row))
                      )
                    }
                  />
                  <Input
                    value={phraseOther[idx] ?? ""}
                    onChange={(e) =>
                      setPhraseOther((prev) =>
                        prev.map((row, i) => (i === idx ? e.target.value : row))
                      )
                    }
                    placeholder="Other hazard phrase / free text"
                  />
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                  <div className="space-y-1">
                    <Label>Substance / Agent</Label>
                    <Input
                      value={hazard.substance_or_agent ?? ""}
                      onChange={(e) =>
                        applyAgentSuggestions(idx, e.target.value, hazard.category)
                      }
                      placeholder="e.g. isocyanates (required if no hazard phrase)"
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
                      placeholder="Auto-fills from agent when known — override freely"
                    />
                  </div>
                </div>

                <div className="space-y-1">
                  <Label>Potential Health Effects (select all that apply)</Label>
                  <MultiCheck
                    idPrefix={`he-${idx}`}
                    options={HEALTH_EFFECT_OPTIONS}
                    selected={effectsSelected[idx] ?? []}
                    onChange={(next) =>
                      setEffectsSelected((prev) =>
                        prev.map((row, i) => (i === idx ? next : row))
                      )
                    }
                  />
                  <Input
                    value={effectsOther[idx] ?? ""}
                    onChange={(e) =>
                      setEffectsOther((prev) =>
                        prev.map((row, i) => (i === idx ? e.target.value : row))
                      )
                    }
                    placeholder="Other health effects"
                  />
                </div>

                <div className="space-y-1">
                  <Label>Existing Control Measures (select all that apply)</Label>
                  <MultiCheck
                    idPrefix={`cm-${idx}`}
                    options={CONTROL_MEASURE_OPTIONS}
                    selected={controlsSelected[idx] ?? []}
                    onChange={(next) =>
                      setControlsSelected((prev) =>
                        prev.map((row, i) => (i === idx ? next : row))
                      )
                    }
                  />
                  <Input
                    value={controlsOther[idx] ?? ""}
                    onChange={(e) =>
                      setControlsOther((prev) =>
                        prev.map((row, i) => (i === idx ? e.target.value : row))
                      )
                    }
                    placeholder="Other controls"
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
                  setRiskAssessment({
                    ...riskAssessment,
                    risk_assessment_completed: v === true,
                  })
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
                  setRiskAssessment({
                    ...riskAssessment,
                    workers_consulted: v === true,
                  })
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
                    setRiskAssessment({
                      ...riskAssessment,
                      risk_assessment_date: e.target.value,
                    })
                  }
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="ra-assessor">Assessor Name</Label>
                <Input
                  id="ra-assessor"
                  value={riskAssessment.assessor_name ?? ""}
                  onChange={(e) =>
                    setRiskAssessment({
                      ...riskAssessment,
                      assessor_name: e.target.value,
                    })
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
