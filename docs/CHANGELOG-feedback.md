# Changelog — Feedback UX

All notable changes from reviewer feedback in [`feedback/feedback.docx`](../feedback/feedback.docx)
and [`feedback/Feedabck-v3.docx`](../feedback/Feedabck-v3.docx).

Format based on [Keep a Changelog](https://keepachangelog.com/).

## [Unreleased] — Feedback v3 (2026-07-15)

### Added

#### Individual risk & wet work
- Assessment scope (`staff_group` | `individual`) and pre-existing conditions catalog on the org form.
- Wet-work hand washes/day + `surveillance_level` (`lower` | `higher`); >20 washes auto-suggests high exposure and higher-level HS.

#### HSE five steps & clear form
- Form section titles aligned to HSE steps (identify → assess → control → record → review).
- Clear form button resets UI and live draft for a fresh workflow.
- Organisation name optional (anonymous use → `Anonymous organisation`).

#### Hierarchy of controls & resources
- Control catalog reordered to HoC (elimination → PPE last; HS as administrative).
- Workflow/ACT prompts: HoC, SEQOHS 3.2/5.2, referral boundaries, training URL guidance.
- Curated **Resources for human review** on Workflows results (HSE, SEQOHS, ARTP, BSA).

#### PII masking
- Always-on regex masking with OpenAI Privacy Filter placeholder taxonomy (`[PRIVATE_EMAIL]`, etc.).
- Optional `OH_PII_PROVIDER=opf` after installing [openai/privacy-filter](https://github.com/openai/privacy-filter) locally (see `.env.example` / `docs/LOCAL_SETUP.md`).

### Out of scope (v3)
- Fully offline / on-prem surveillance upload.
- Separate full dual “staff group vs individual” product modes (scope toggle only).

---

## [Unreleased] — Feedback UX (2026-07-13)

### Added

#### Form (T1)
- Static option catalogs for sector, sector-aware key tasks, workforce characteristics, hazard phrases, health effects, and control measures (`frontend/src/lib/form-options.ts`).
- Exposure level and frequency definition helper text under the corresponding selects.
- Overrideable WEL and potential-health-effect suggestions based on substance/agent and hazard category.
- Vitest coverage for catalog helpers (`frontend/src/lib/form-options.test.ts`).

#### Persistence (T5)
- Live form draft in `sessionStorage` so organisation/hazard input survives navigation across pages (`frontend/src/lib/form-draft.ts`).
- Named draft history in `localStorage` with Save draft / Load draft / Clear history in the shared form header.
- Vitest coverage for storage helpers with an in-memory `Storage` mock (`frontend/src/lib/form-draft.test.ts`).

#### CHECK / REVIEW (T4)
- Compliance audit indicators: `methodology_assessed` and `escalation_process_assessed` (backend model, agent prompt/parse, UI).
- Trend Analysis anonymisation alert (PII and small-cell triangulation risk) above the surveillance summary.
- Trend agent prompt line to flag identifiable data.

#### Prompts (T3)
- Module-level `WORKFLOW_CONSISTENCY_RULES` injected into workflow generation (canonical terminology, consistent roles, OHT administer vs OH professional interpret).
- Guardrail MUST bullets for role consistency, safe delegation, and `audiometry` (not “hearing test”).
- Clarifying copy on the Workflows page: Surveillance Provisions vs Workflow Steps.

#### Models (T2)
- `DeliveryModel.none` — “No OH service currently in place”.

### Changed

#### Form (T1 / T2)
- Sector → dropdown (+ Other); key tasks → multi-select (+ Other).
- Label “Workforce Size” → “Number of workers exposed”.
- Label “Delivery Model” → “Model of OH Delivery”.
- Workforce characteristics, hazard phrases, health effects, and existing controls → multi-select (+ Other).
- Hazard phrase is optional; at least one of hazard phrase or substance/agent is required.
- When `showRiskAssessment` is true, org-level PLAN confirmation checkboxes are hidden and synced from the dedicated Risk Assessment Confirmation block (single source of truth).

### Fixed
- Draft “Load draft” `Select` `onValueChange` typing (`string | null`) so `npm run build` succeeds on Next.js.

### Out of scope
- Video/picture hazard uploads (blue-sky feedback).
- Server-side run history / accounts.
- Full demographic workforce questionnaire.
- Dedicated `/benchmark` or `/gap-analysis` UI pages.

---

## By area

| Area | Summary | Tasks |
|------|---------|-------|
| Workflow Generator form | Catalogs, labels, multi-selects, exposure definitions, WEL/effects suggest | T1, T2 |
| Form persistence | Cross-page live draft + named history | T5 |
| PDCA prompts / copy | Role & terminology consistency; section clarify | T3 |
| Compliance / Trend | New indicators; PII warning | T4 |
| Build | Select value type for draft loader | — |

## Files touched

**Frontend:** `org-hazard-form.tsx`, `form-options.ts`, `form-draft.ts`, `types.ts`, `workflows/page.tsx`, `compliance-audit/page.tsx`, `trend-analysis/page.tsx`, Vitest config + tests, `package.json`

**Backend:** `models/organisation.py`, `models/hazard.py`, `models/workflow.py`, `agents/workflow_agent.py`, `agents/guardrails.py`, `agents/benchmark_agent.py`

**Tests:** `tests/test_models.py`, `tests/test_guardrails.py`, `tests/test_benchmark_agent.py`
