# Grants Manager Assistant System (GMAS) - Implementation Plan

**Document**: 04_Implementation_Plan
**Version**: 1.2.0
**Created**: 2026-06-23
**Modified**: 2026-06-23
**Status**: DRAFT — AWAITING OWNER REVIEW

**Change from v1.1.0**: Fiscal sponsor model added (Section 9.4); Funder and Grant models updated with fiscal sponsor flags and per-grant sponsor selection; seed_data.py redesigned as a loader from `org_profile_seed_data.md` (configurable, multi-org capable).

**Scope**: Phases 1–6 (Foundation → Approval Gate + Reporting). Phases 7 (Ollama) and 8 (Docker/Cloud) deferred.
**AI Engine (Development Only)**: Claude Sonnet 4.6 — used to BUILD, not to RUN.
**Tech Stack**: Python · Streamlit · SQLAlchemy · SQLite · Pandas · Plotly · Jinja2 · conda

---

## 1. Purpose

This document is the execution contract for the Claude Code agent team that will generate the GMAS v1.1.0 application code. It translates the SDLC artifacts (PRD v1.1.0, HLD v1.1.0, Detailed Design v1.1.0) into a sequenced, agent-ready task breakdown.

**Agents must treat the SDLC specifications as detailed guidance** — implement exactly what is specified where it is clear; apply sound judgment for gaps and edge cases while staying true to the intent of the specifications. No backward-compatibility shims, no unused scaffolding, no features beyond the defined scope.

---

## 2. Confirmed Decisions

| Question | Decision |
|----------|----------|
| Org Profile Seed Data | Use actual Dojo at Somernova data (Section 9) coded into a markdown file named "org_profile_seed_data.md".  From day one we DO NOT want to hard-code org-specific data into the application.  We want to design the system to be configurable and useable for other organizations grants management work.  So turn  seed_data.py into a LOADER that gets the organizational context information from a structured org profile document. |
| Implementation Scope | Option B: Phases 1–6 only. Ollama (Phase 7) and Docker/Cloud (Phase 8) are deferred. |
| Agent Fidelity | Detailed guidance. Agents may make reasonable implementation decisions within the spirit of the SDLC specs. |
| File Versioning | Never overwrite existing files. All new/modified files must include datetime stamps and semantic version headers. |
| Multi-Agent Approach | Allowed and expected. Use parallel agents for code generation, documentation, and review, and version control. |

---

## 3. Scope Boundaries

### In Scope (Phases 1–6)
- Phase 1: Organization profile, grant repository, deadline tracker, grant dashboard
- Phase 2: Rules-based scoring engine, hard filter rules, deduplication, criteria editor
- Phase 3: Template library (paragraph templates, variable substitution)
- Phase 4: Application lifecycle, draft versioning, document requirements, manifest
- Phase 5: Four-category structured human review pipeline (checklists, blocking logic)
- Phase 6: Hard approval gate, submission logging, weekly report (Jinja2), analytics, funders page, settings page

### Explicitly Out of Scope for This Build
- Phase 7: Ollama local AI integration (deferred)
- Phase 8: Docker containerization, cloud deployment, CI/CD (deferred)
- Google Docs publishing integration (settings placeholder only — no implementation)
- Multi-user / role-based access
- CSV/Excel import (manual entry only for MVP — import UI placeholder is acceptable)
- Email/calendar integrations

---

## 4. File and Version Management Convention

**RULE: Never overwrite an existing file. Always create new files.**

### New Files Created by Agents
Include this header block at the top of every new source file:

```python
# ============================================================
# File: <relative path from project root>
# Version: 1.1.0
# Created: 2026-06-23
# Modified: 2026-06-23
# Description: <one-line purpose>
# ============================================================
```

For Markdown/Jinja2 files, use a comment equivalent or YAML frontmatter block.

### Naming Convention for Generated Files
- Source files: standard Python naming (`snake_case.py`)
- Generated SDLC documents: `NN_DocumentName_vX.Y.Z.md` (e.g., `05_Testing_Plan_v1.1.0.md`)
- No `_copy`, `_backup`, `_old` suffixes — use semantic versions instead
- If a file at a path already exists, bump the minor version: `v1.1.0` → `v1.2.0`

---

## 5. Project Directory Structure to Create

Agents must create this exact structure. Files that are agent-generated are marked (A):

```
Grants_Assistant/
├── src/
│   ├── app/
│   │   ├── main.py                       (A) Streamlit entry point
│   │   ├── pages/
│   │   │   ├── 01_dashboard.py           (A)
│   │   │   ├── 02_enter_grant.py         (A)
│   │   │   ├── 03_grants.py              (A)
│   │   │   ├── 04_applications.py        (A)
│   │   │   ├── 05_reports.py             (A)
│   │   │   ├── 06_funders.py             (A)
│   │   │   ├── 07_analytics.py           (A)
│   │   │   └── 08_settings.py            (A)
│   │   └── components/
│   │       ├── grant_card.py             (A)
│   │       ├── urgency_badge.py          (A)
│   │       ├── review_status_panel.py    (A)
│   │       ├── approval_gate.py          (A)
│   │       └── score_breakdown.py        (A)
│   │
│   ├── engine/
│   │   ├── scoring_engine.py             (A)
│   │   ├── deadline_classifier.py        (A)
│   │   ├── deduplication.py              (A)
│   │   ├── state_machine.py              (A)
│   │   └── template_renderer.py          (A)
│   │
│   ├── models/
│   │   ├── __init__.py                   (A) imports all models
│   │   ├── organization.py               (A)
│   │   ├── grant.py                      (A)
│   │   ├── funder.py                     (A)
│   │   ├── selection_criteria.py         (A)
│   │   ├── application.py                (A)
│   │   ├── draft.py                      (A)
│   │   ├── review.py                     (A)
│   │   ├── manifest.py                   (A)
│   │   ├── template.py                   (A)
│   │   ├── report.py                     (A)
│   │   └── org_document.py               (A)
│   │
│   ├── services/
│   │   ├── grant_service.py              (A)
│   │   ├── scoring_service.py            (A) thin wrapper — calls ScoringEngine
│   │   ├── application_service.py        (A)
│   │   ├── review_service.py             (A)
│   │   ├── report_service.py             (A)
│   │   ├── manifest_service.py           (A)
│   │   └── funder_service.py             (A)
│   │
│   ├── db/
│   │   ├── database.py                   (A)
│   │   ├── seed_data.py                  (A) — loader, not hard-coded; reads org_profile_seed_data.md
│   │   ├── org_profile_loader.py         (A) — parses org profile Markdown into Python dicts
│   │   └── migrations/                   (A) Alembic migrations
│   │
│   ├── templates/
│   │   ├── reports/
│   │   │   └── weekly_report.md.j2       (A)
│   │   ├── drafts/                       (A) paragraph template text files (optional — templates stored in DB)
│   │   └── checklists/
│   │       └── default_checklist_items.py (A) default item definitions for all 4 review types
│   │
│   └── utils/
│       ├── config.py                     (A)
│       ├── logger.py                     (A)
│       ├── error_handler.py              (A)
│       └── export.py                     (A) Markdown and PDF export helpers
│
├── tests/
│   ├── conftest.py                       (A)
│   ├── unit/
│   │   ├── test_scoring_engine.py        (A)
│   │   ├── test_deadline_classifier.py   (A)
│   │   ├── test_deduplication.py         (A)
│   │   ├── test_state_machine.py         (A)
│   │   ├── test_template_renderer.py     (A)
│   │   ├── test_grant_service.py         (A)
│   │   ├── test_application_service.py   (A)
│   │   ├── test_review_service.py        (A)
│   │   ├── test_report_service.py        (A)
│   │   └── test_manifest_service.py      (A)
│   └── integration/
│       ├── test_full_grant_lifecycle.py  (A)
│       ├── test_report_generation.py     (A)
│       └── test_status_transitions.py    (A)
│
├── data/
│   ├── org_profile/
│   │   └── org_profile_seed_data.md      (A) structured Markdown — Dojo profile per Section 9
│   ├── org_documents/                    (A) empty dir — for uploaded docs
│   ├── exports/                          (A) empty dir — for generated reports
│   └── backups/                          (A) empty dir — for DB backups
│
├── logs/                                 (A) empty dir — created at runtime
├── .env.example                          (A)
├── requirements.txt                      (A) — NO anthropic SDK
├── pyproject.toml                        (A)
└── alembic.ini                           (A)
```

---

## 6. Parallel Development Tracks

### Track A — Database & Infrastructure
**Owner**: Infrastructure Agent
**Outputs**: All models, migrations, org profile Markdown file, org profile loader, seed_data.py, utilities (config, logger, error handler)
**Milestone**: `alembic upgrade head && python src/db/seed_data.py` completes without error; org profile, fiscal sponsors, priority funders, and default criteria appear in DB

### Track B — Streamlit UI
**Owner**: UI Agent
**Outputs**: main.py, all 8 pages, all components
**Milestone**: `streamlit run src/app/main.py` launches with all 8 pages rendering (stubs acceptable for service calls in early phases)
**Dependency**: Track A must deliver model type stubs before Track B pages wire to services

### Track C — Business Logic
**Owner**: Logic Agent
**Outputs**: All engine modules, all service modules, Jinja2 report template
**Milestone**: All services can be instantiated against the seeded DB; scoring engine produces correct results for test inputs
**Dependency**: Track A models must be available

### Track D — Testing
**Owner**: Test Agent
**Outputs**: conftest.py, all unit and integration tests
**Milestone**: `pytest tests/` runs clean with ≥ 80% coverage on all service and engine modules
**Dependency**: Track A + C for unit tests; A + B + C for integration tests

### Track E — Documentation (Deferred — Lower Priority)
**Owner**: Doc Agent (Phase 6+)
**Outputs**: User Guide (weekly cycle), Technical Reference
**Milestone**: Markdown docs in `docs/` directory
**Note**: Start only after Phases 1–5 are functionally complete

---

## 7. Phase Sequence and Milestones

```
PHASE 0 — Project Setup (Track A alone)
  └─ Deliverable: Working project skeleton, conda environment.yml, requirements.txt, alembic init

PHASE 1 — Foundation (Tracks A + B in parallel)
  ├─ Track A: All models, initial migration, seed data
  └─ Track B: main.py, Dashboard, Enter Grant, Grant Database pages + components

    [Integration Checkpoint 1]
    Track C starts. Track B wires Grant pages to GrantService.

PHASE 2 — Rules Engine (Track C; Track D begins unit tests)
  ├─ Track C: scoring_engine, deadline_classifier, deduplication, state_machine
  ├─ Track C: GrantService (create, score, filter, soft delete)
  └─ Track D: Unit tests for all Phase 2 engine modules

PHASE 3 — Template Library (Track C; Track D continues)
  ├─ Track C: template_renderer, Template model seeded, paragraph templates
  └─ Track D: Unit tests for template_renderer, GrantService

    [Integration Checkpoint 2]
    Track B wires Applications page to ApplicationService stubs.

PHASE 4 — Application Management (Tracks A + B + C)
  ├─ Track A: DraftVersion, DocumentRequirement, Manifest models + migration
  ├─ Track B: Applications page — Overview, Documents, Draft Editor tabs
  ├─ Track C: ApplicationService (create, draft, lifecycle), ManifestService
  └─ Track D: Unit tests for ApplicationService (lifecycle, no hard gate yet)

PHASE 5 — Review Pipeline (Tracks B + C)
  ├─ Track B: Applications page — Reviews tab (4 sub-tabs), review_status_panel component
  ├─ Track C: ReviewService (checklists, items, assumption/ambiguity records, blocking logic)
  └─ Track D: Unit tests for ReviewService; checklist blocking tests

PHASE 6 — Approval Gate + Reporting (Tracks B + C; Track D integration tests)
  ├─ Track B: approval_gate component, Reports page, Funders page, Analytics page, Settings page
  ├─ Track C: Hard gate in ApplicationService.approve_application(), ReportService + weekly_report.j2, FunderService
  ├─ Track D: Hard gate enforcement tests, integration tests for full lifecycle + report generation
  └─ Track E: User guide and technical reference (if time permits)

    [Final Integration Checkpoint]
    Full end-to-end test: enter grant → score → approve to apply → draft → 4 reviews → approve → submit
```

---

## 8. Detailed Task Specifications per Track

### 8.1 Track A — Database & Infrastructure

#### Phase 0 Tasks

**A-P0-01**: Create `pyproject.toml`
```toml
[project]
name = "gmas"
version = "1.1.0"
requires-python = ">=3.11"

[tool.ruff]
line-length = 100
target-version = "py311"

[tool.mypy]
python_version = "3.11"
strict = true
ignore_missing_imports = true
```

**A-P0-02**: Create `requirements.txt` — no `anthropic` package
```
streamlit>=1.35.0
sqlalchemy>=2.0.0
alembic>=1.13.0
pandas>=2.2.0
plotly>=5.20.0
jinja2>=3.1.0
pydantic-settings>=2.0.0
httpx>=0.27.0
weasyprint>=62.0
python-dotenv>=1.0.0
pytest>=8.0.0
pytest-mock>=3.0.0
ruff>=0.4.0
mypy>=1.10.0
```

**A-P0-03**: Create `src/utils/config.py` — pydantic-settings Settings class per DD Section 2.7.1

**A-P0-04**: Create `src/utils/logger.py` — rotating file logger per DD Section 2.7.2

**A-P0-05**: Create `src/utils/error_handler.py` — all custom exceptions per DD Section 2.7.3:
`GmasError`, `SubmissionBlockedError`, `InvalidStatusTransitionError`, `DuplicateGrantError`, `ValidationError`, `IntegrationDisabledError`

**A-P0-06**: Create `src/db/database.py` — engine, SessionLocal, Base, get_db(), init_db() per DD Section 2.1.1

**A-P0-07**: Initialize Alembic: `alembic init src/db/migrations`. Configure `env.py` to import `Base.metadata` from `src.models`. Add pre-migration SQLite backup hook.

**A-P0-08**: Create `.env.example` per DD Section 2.7.1 (no API keys required)

#### Phase 1 Tasks (Models)

**A-P1-01**: `src/models/organization.py` — Organization, OrgDocument per DD Section 2.2.1 and HLD Section 4.2

**A-P1-02**: `src/models/funder.py` — Funder with funder_type ENUM (foundation, government, corporate, other, community_partner). Add two boolean flags:
- `is_fiscal_sponsor: bool` — True if this org can serve as a fiscal sponsor for the Dojo
- `is_501c3: bool` — True if this org holds its own 501(c)(3) status (relevant for fiscal sponsors, since only 501c3 fiscal sponsors unlock grants requiring 501c3)

**A-P1-03**: `src/models/selection_criteria.py` — SelectionCriteria with criteria_json, is_active, version

**A-P1-04**: `src/models/grant.py` — Grant with full status ENUM, VALID_TRANSITIONS dict, all columns per HLD Section 4.2. Add one optional field:
- `fiscal_sponsor_id: UUID FK → funders` (nullable) — the specific fiscal sponsor selected for this grant. If NULL, the org's default fiscal sponsor (from eligibility_json) is assumed. This enables per-grant fiscal sponsor selection.

**A-P1-05**: `src/models/__init__.py` — imports all models so Alembic sees metadata

**A-P1-06**: Create Alembic migration `001_initial_schema.py` — all tables from Phase 1 models

**A-P1-07**: Three files to create together:
- `data/org_profile/org_profile_seed_data.md` — structured Markdown file with the Dojo's profile data per **Section 9**. Format: YAML frontmatter for scalar fields, Markdown sections for multi-value fields (programs, partners, criteria, templates). Must be human-editable by non-developers.
- `src/db/org_profile_loader.py` — parses `org_profile_seed_data.md` and returns typed Python dicts. Validates required fields and raises `ConfigurationError` with clear messages if required fields are missing.
- `src/db/seed_data.py` — calls `org_profile_loader.load(path)`, then inserts Organization, SelectionCriteria, Funder, and Template records. Idempotent: checks existence by org name before inserting. Accepts optional `--profile` CLI arg to load a different org profile file (enables multi-org use).

#### Phase 4 Tasks (Additional Models)

**A-P4-01**: `src/models/application.py` — Application, DocumentRequirement; ENUM for application status and outcome

**A-P4-02**: `src/models/draft.py` — DraftVersion with sections_json

**A-P4-03**: `src/models/review.py` — ReviewChecklist, ChecklistItem, AssumptionRecord, AmbiguityRecord

**A-P4-04**: `src/models/manifest.py` — Manifest with events_json (append-only array)

**A-P4-05**: `src/models/template.py` — Template with category, body, variables_json, is_system, version

**A-P4-06**: `src/models/report.py` — WeeklyReport

**A-P4-07**: Create Alembic migration `002_application_models.py` — all Phase 4 tables

**A-P4-08**: Extend `seed_data.py` to seed 15+ paragraph templates per **Section 10 of this document**. Add default checklist items for all 4 review types per **Section 11 of this document**.

---

### 8.2 Track B — Streamlit UI

#### Phase 1 Tasks

**B-P1-01**: `src/app/main.py` — st.set_page_config, custom CSS for urgency badges (RED/YELLOW/GREEN/GRAY), template-fill class per DD Section 2.5.1

**B-P1-02**: `src/app/components/urgency_badge.py` — renders colored HTML badge for a DeadlineUrgency value

**B-P1-03**: `src/app/components/grant_card.py` — compact grant summary card per DD Section 2.5.2

**B-P1-04**: `src/app/components/score_breakdown.py` — expander showing criterion-level score breakdown from score_breakdown_json

**B-P1-05**: `src/app/pages/01_dashboard.py` — 5 metric cards, urgency widget, recent activity feed, quick actions per DD Section 2.5.3

**B-P1-06**: `src/app/pages/02_enter_grant.py` — Manual entry form with all metadata fields, deduplication warning display, URL and date validation. CSV import tab: placeholder UI with "Coming Soon" message.

The form must include a **Fiscal Sponsor** field that appears when `eligibility_501c3_required == True`:
- Dropdown populated from `Funder` records where `is_fiscal_sponsor == True`
- Default selection: Teen Empowerment (the primary fiscal sponsor)
- Label: "Fiscal Sponsor for this application (if 501c3 required)"
- If the user selects "None" and the grant requires 501c3 with no fiscal sponsorship allowed, the system shows a warning: "The Dojo cannot apply to this grant without a fiscal sponsor." The grant can still be saved but will receive a score of 0.0.

**B-P1-07**: `src/app/pages/03_grants.py` — Sidebar filters, sortable/filterable grant table, per-row action buttons (View · Edit · Create Application · Archive)

#### Phase 3–4 Tasks

**B-P3-01**: `src/app/pages/04_applications.py` — Application list view + detail view with 5 tabs: Overview · Documents · Draft Editor · Reviews · Manifest (tabs may be stubs initially)

**B-P3-02**: Draft Editor tab — left sidebar template browser (by category), section-by-section draft form, word count display, "Save Draft" button. Distinguish template-fill content visually (light blue left border per CSS).

#### Phase 5 Tasks

**B-P5-01**: `src/app/components/review_status_panel.py` — 4-column status display per DD Section 2.5.2

**B-P5-02**: Reviews tab in Applications page — 4 sub-tabs (Fact Verification · Assumption Log · Ambiguity Resolution · Compliance). Each sub-tab renders its checklist items with checkboxes, finding notes, and status. Assumption Log and Ambiguity Resolution tabs include "Add Record" forms.

#### Phase 6 Tasks

**B-P6-01**: `src/app/components/approval_gate.py` — per DD Section 2.5.2. Shows blockers when not all reviews are complete; shows pre-submission acknowledgment checklist and approval button when all conditions met.

**B-P6-02**: `src/app/pages/05_reports.py` — "Generate Weekly Report" button with preview, historical report list, Markdown and PDF download buttons, Google Docs button (placeholder — shows "Integration not configured" if not set up).

**B-P6-03**: `src/app/pages/06_funders.py` — Funder list with per-funder grant history (grants applied, awarded, total funding). Add/Edit funder form.

**B-P6-04**: `src/app/pages/07_analytics.py` — Plotly charts: grants by status, total funding requested vs. awarded, win rate by focus area. All charts interactive. Data from DB on each page load (no cache).

**B-P6-05**: `src/app/pages/08_settings.py` — 4 tabs:
- **Organization**: edit org profile fields
- **Criteria**: criteria editor with weight sliders, hard filter toggles, named rule sets, live score preview
- **Templates**: template table, inline editor, variable helper (click to insert `{{variable}}`)
- **Integrations**: Ollama status (shows "Not configured — Phase 7 feature"), Google Docs status (shows "Not configured" with setup instructions)

---

### 8.3 Track C — Business Logic

#### Phase 2 Tasks

**C-P2-01**: `src/engine/deadline_classifier.py` — `classify_urgency(deadline)` and `days_until_deadline(deadline)` per DD Section 2.3.2. Past deadlines return GRAY (not error).

**C-P2-02**: `src/engine/deduplication.py` — `find_duplicates(candidate, existing_grants)` per DD Section 2.3.3. Returns matches with `match_type` ("exact" or "fuzzy") and `match_field`.

**C-P2-03**: `src/engine/state_machine.py` — `advance_status(current, new)` per DD Section 2.3.4. Raises `InvalidStatusTransitionError` for invalid transitions. Uses `VALID_TRANSITIONS` dict from `grant.py`.

**C-P2-04**: `src/engine/scoring_engine.py` — full `ScoringEngine` class per DD Section 2.3.1. Must implement:
- `score_grant(grant, criteria, org) -> ScoreResult`
- `_evaluate_criterion(rule, grant, org) -> CriterionResult`
- Individual evaluators: `_eval_geography`, `_eval_focus_area`, `_eval_eligibility`, `_eval_amount_range`
- Hard filter short-circuit before weighted scoring
- `ScoreResult` and `CriterionResult` dataclasses

**Eligibility evaluator logic** (updated for fiscal sponsor model):
```
_eval_eligibility(rule, grant, org):
  has_own_501c3 = org.eligibility_json["has_501c3"]  # False for the Dojo
  grant_requires_501c3 = grant.eligibility_501c3_required
  grant_allows_fiscal = grant.fiscal_sponsorship_allowed

  # Determine if a fiscal sponsor is available for this specific grant
  grant_has_fiscal_sponsor = (grant.fiscal_sponsor_id is not None)
  org_has_default_fiscal_sponsor = bool(org.eligibility_json.get("default_fiscal_sponsor"))
  fiscal_sponsor_available = grant_has_fiscal_sponsor or org_has_default_fiscal_sponsor

  if not grant_requires_501c3:
      return PASS  # No 501c3 requirement at all
  if has_own_501c3:
      return PASS  # Org has its own 501c3
  if grant_allows_fiscal and fiscal_sponsor_available:
      return PASS  # Can apply through fiscal sponsor
  if grant_allows_fiscal and not fiscal_sponsor_available:
      return PARTIAL (0.5)  # Fiscal sponsor allowed but none configured
  # grant_requires_501c3 AND not allows_fiscal AND org has no 501c3
  return FAIL  # Hard filter blocks this grant → score 0.0
```

**C-P2-05**: `src/services/grant_service.py` — `GrantService` class with:
- `create_grant(data) -> Grant` — validates, dedup checks, scores, classifies urgency, advances to EVALUATED or RECOMMENDED
- `get_grants_paginated(filters, page, page_size) -> Page[Grant]`
- `advance_status(grant_id, new_status) -> Grant`
- `soft_delete(grant_id) -> None`
- `re_score_all(criteria_id) -> int`

**C-P2-06**: `src/services/scoring_service.py` — thin wrapper: `score_grant(grant_id, db)` fetches active criteria and org, calls `ScoringEngine.score_grant()`, persists `fit_score` and `score_breakdown_json` to grant record.

#### Phase 3 Tasks

**C-P3-01**: `src/engine/template_renderer.py` — `render_template(body, context)` per DD Section 2.3.5. Unknown `{{variables}}` become `[FILL IN: variable_name]`. `build_org_context(org) -> dict` helper.

**C-P3-02**: `src/templates/checklists/default_checklist_items.py` — Python dict of default checklist item definitions for all 4 review types per DD Section 3.3. Used by ReviewService when initializing checklists.

#### Phase 4 Tasks

**C-P4-01**: `src/services/manifest_service.py` — `ManifestService` per DD Section 2.4.5:
- `create_manifest(db, application_id) -> Manifest`
- `append_event(db, application_id, event_type, details) -> None`
- `export_markdown(db, application_id) -> str`

**C-P4-02**: `src/services/application_service.py` — `ApplicationService` per DD Section 2.4.2, EXCEPT the hard gate in `approve_application()` is implemented in Phase 6:
- `create_application(grant_id) -> Application` — creates Application, DocumentRequirement checklist, Manifest; advances grant to APPROVED_TO_APPLY
- `create_draft_version(application_id, sections) -> DraftVersion` — auto-increments version number; appends manifest event
- `record_submission(application_id, method, confirmation, submitter) -> Application`
- `record_outcome(application_id, outcome, award_amount) -> Application`

**C-P4-03**: `src/services/funder_service.py` — CRUD for Funder records + per-funder history aggregation

#### Phase 5 Tasks

**C-P5-01**: `src/services/review_service.py` — `ReviewService` per DD Section 2.4.3:
- `initialize_checklists(application_id, draft_version_id) -> list[ReviewChecklist]` — creates 4 checklists with default items
- `update_checklist_item(item_id, is_checked, finding) -> ChecklistItem` — updates item; re-evaluates parent checklist blocking status
- `add_assumption(checklist_id, description, basis, is_documented) -> AssumptionRecord`
- `add_ambiguity(checklist_id, description, resolution, decision) -> AmbiguityRecord`
- `complete_checklist(checklist_id, reviewer_name) -> ReviewChecklist` — sets COMPLETED or BLOCKED based on critical items

#### Phase 6 Tasks

**C-P6-01**: Add `approve_application(application_id, approver_name) -> Application` to `ApplicationService` — this is the hard gate per DD Section 2.4.2 and PRD FR-AG-001 through FR-AG-004:
- Check all 4 review checklists are COMPLETED for the current draft
- Check no checklist has `has_blocking_items = True`
- If either check fails → raise `SubmissionBlockedError` with specific reason
- If both pass → record approval, advance status to APPROVED, append manifest event

**C-P6-02**: `src/services/report_service.py` — `ReportService` per DD Section 2.4.4:
- `generate_weekly_report(db, org) -> WeeklyReport` — builds context dict, renders `weekly_report.md.j2`, stores result
- `export_pdf(report, output_path) -> str` — Markdown → HTML → PDF via weasyprint
- `export_markdown(report, output_path) -> str`

**C-P6-03**: `src/templates/reports/weekly_report.md.j2` — full Jinja2 template per DD Section 3.1. All 5 sections. Use `{{ grant.amount_min | int }}` formatting. Handle null deadlines gracefully.

**C-P6-04**: `src/utils/export.py` — helpers for Markdown-to-HTML conversion and PDF generation

---

### 8.4 Track D — Testing

#### Setup (starts Phase 2)

**D-SETUP-01**: `tests/conftest.py` — fixtures per DD Section 4.5:
- `db()` — in-memory SQLite, creates all tables, seeds test data
- `sample_grant(db)` — returns an EVALUATED Grant with fit_score 8.5
- `sample_application(db, sample_grant)` — Application with no reviews started
- `sample_application_fully_reviewed(db, sample_grant)` — Application where all 4 checklists are COMPLETED with no blocking items

#### Unit Tests (Phase 2–5)

**D-UT-01**: `tests/unit/test_scoring_engine.py`
- Hard filter fails → score 0.0, `hard_filter_failed=True`
- All criteria match → score 10.0
- Partial match → correct weighted sum
- Geography evaluator: exact match, partial match, no match
- Eligibility evaluator: 501c3 required + no fiscal sponsor → fails hard filter; fiscal sponsor allowed → passes
- Score breakdown JSON has correct structure

**D-UT-02**: `tests/unit/test_deadline_classifier.py`
- 25 days → RED
- 45 days → YELLOW
- 75 days → GREEN
- 120 days → GRAY
- None → GRAY
- -5 days (past) → GRAY

**D-UT-03**: `tests/unit/test_deduplication.py`
- Same URL → exact match
- Same name + funder → exact match
- Similar name (>0.85 similarity) + same funder → fuzzy match
- Different funder → no match

**D-UT-04**: `tests/unit/test_state_machine.py`
- All valid transitions from VALID_TRANSITIONS pass
- Invalid transition (e.g., DISCOVERED → SUBMITTED) raises `InvalidStatusTransitionError`

**D-UT-05**: `tests/unit/test_template_renderer.py`
- Known variable → replaced
- Unknown variable → `[FILL IN: variable_name]`
- Empty context → all unknowns flagged
- `build_org_context` returns dict with all expected keys

**D-UT-06**: `tests/unit/test_grant_service.py`
- create_grant → status EVALUATED, fit_score set, urgency set
- create_grant → RECOMMENDED if score ≥ 7
- create_grant duplicate → raises `DuplicateGrantError`
- soft_delete → is_deleted=True, not returned in paginated query
- re_score_all → updates scores for all non-terminal grants

**D-UT-07**: `tests/unit/test_application_service.py`
- create_application → Application created, DocumentRequirements populated, Manifest created
- create_draft_version → DraftVersion with auto-incremented version number
- approve_application (no reviews) → raises `SubmissionBlockedError`
- approve_application (blocking items) → raises `SubmissionBlockedError`
- approve_application (all conditions met) → status APPROVED, approved_by set

**D-UT-08**: `tests/unit/test_review_service.py`
- initialize_checklists → 4 checklists created with correct review_types
- initialize_checklists → default items seeded for each checklist
- update_checklist_item (critical, unchecked) → parent checklist = BLOCKED
- complete_checklist (all critical items checked) → status COMPLETED
- complete_checklist (critical item unchecked) → status BLOCKED

**D-UT-09**: `tests/unit/test_report_service.py`
- generate_weekly_report → WeeklyReport created with non-empty content_markdown
- content includes all 5 sections
- Recommended grants (score ≥ 7) appear in Sections 3 and 4

**D-UT-10**: `tests/unit/test_manifest_service.py`
- create_manifest → Manifest created with APPLICATION_CREATED event
- append_event → event appended to events_json (does not overwrite previous events)
- export_markdown → returns valid Markdown string with event table

#### Integration Tests (Phase 6)

**D-IT-01**: `tests/integration/test_full_grant_lifecycle.py`
- Full path: `create_grant` → `create_application` → `create_draft_version` → `initialize_checklists` → complete all 4 checklists → `approve_application` → `record_submission` → `record_outcome(AWARDED)` 
- Verify final grant status is AWARDED
- Verify manifest has all expected events in order

**D-IT-02**: `tests/integration/test_report_generation.py`
- Seed 10 grants with varied scores and urgencies
- Call `generate_weekly_report`
- Verify: all 5 sections present, grants sorted by fit_score, recommended count correct

**D-IT-03**: `tests/integration/test_status_transitions.py`
- Walk all valid transition paths from DISCOVERED to AWARDED
- Verify every invalid transition raises `InvalidStatusTransitionError`

---

### 8.5 Track E — Documentation (Phase 6+)

**E-DOC-01**: `docs/user_guide_weekly_cycle_v1.1.0.md` — Step-by-step weekly workflow:
1. Search for grants (user does this in browser)
2. Enter grants using the Grant Entry page
3. Review auto-scored results on Grant Database page
4. Create applications for recommended grants
5. Use Draft Editor with templates
6. Complete all 4 review checklists
7. Approve and generate submission package
8. Generate weekly report

**E-DOC-02**: `docs/technical_reference_v1.1.0.md` — Developer reference: architecture layers, service API signatures, scoring algorithm, state machine diagram, database schema overview, how to run tests, how to reset/reseed the database.

---

## 9. Seed Data Specifications — The Dojo at Somernova

**Architecture decision (from Section 2)**: `seed_data.py` is a **loader**, not a hard-coded data file. Org-specific data lives in `data/org_profile/org_profile_seed_data.md` — a structured Markdown file that `seed_data.py` parses and loads into the database. This makes GMAS configurable for any organization (not locked to the Dojo).

**What agents must build**:
1. `data/org_profile/org_profile_seed_data.md` — the structured Markdown data file for the Dojo (content specified in Sections 9.1–9.4 below)
2. `src/db/org_profile_loader.py` — parser that reads the Markdown file and returns Python dicts/objects the seeder can insert
3. `src/db/seed_data.py` — calls `org_profile_loader.load("data/org_profile/org_profile_seed_data.md")` then inserts the result into the DB. Must be idempotent (check if org already exists before inserting).

The Markdown file format must be **human-editable and self-documenting**. Use a structured YAML-frontmatter + Markdown-sections format that any non-developer can update to configure the system for a new organization.

**The data in Sections 9.1–9.4 below is the content of `org_profile_seed_data.md` for the Dojo**, expressed as Python for clarity. The loader agent must translate these into the appropriate Markdown schema.

### 9.1 Organization Record

```python
organization = Organization(
    name="The Dojo at Somernova",
    mission=(
        "The Dojo empowers young people through safe, structured, and youth-centered programming "
        "that builds leadership, creativity, workforce readiness, and community connection. "
        "Through mentorship, STEM and climate education, arts and culture, and real-world "
        "opportunities, we help youth develop the skills, confidence, and networks needed to thrive."
    ),
    values_text=(
        "Equity · Multicultural Inclusion · Youth Voice · Community Safety · "
        "Climate Literacy · Economic Mobility"
    ),
    programs_json=[
        {
            "name": "Future Fridays",
            "description": (
                "Weekly drop-in youth program including food, mentorship, guest speakers, "
                "entrepreneurship, financial literacy, and leadership development."
            ),
            "focus_area": "Youth Development",
        },
        {
            "name": "STEM Explorers",
            "description": (
                "Hands-on STEM activities: robotics, coding, engineering challenges, maker "
                "projects, and STEM career exploration. Partners: DLAB, SHS Robotics, local universities."
            ),
            "focus_area": "STEM/STEAM",
        },
        {
            "name": "Climate Leaders Academy",
            "description": (
                "Climate literacy, environmental justice, clean energy careers, sustainability "
                "projects, and community action. Partners: Better Future Project, Greentown Labs, "
                "Somerville Bike Kitchen."
            ),
            "focus_area": "Climate Education",
        },
        {
            "name": "Workforce Ready",
            "description": (
                "Resume building, interview skills, career exploration, job readiness, internship "
                "exposure, and youth stipends."
            ),
            "focus_area": "Workforce Development",
        },
        {
            "name": "Girls in STEM & Climate Innovation",
            "description": (
                "Women mentors, robotics, coding, entrepreneurship, climate technology, and "
                "leadership development for young women ages 13–18."
            ),
            "focus_area": "Girls in STEM",
        },
    ],
    eligibility_json={
        "has_501c3": False,
        "default_fiscal_sponsor": "Teen Empowerment",
        "default_fiscal_sponsor_is_501c3": True,
        "fiscal_sponsorship_accepted": True,
        "target_geographies": ["Massachusetts", "Greater Boston", "Somerville"],
        "target_population": "youth ages 13–18",
        "city": "Somerville",
        "state": "Massachusetts",
        "org_type": "Youth Development Organization (Future 501(c)(3))",
    },
)
```

### 9.2 Default Selection Criteria (Standard Rule Set)

```python
standard_criteria = SelectionCriteria(
    name="Standard",
    version="1.0",
    is_active=True,
    criteria_json=[
        {
            "name": "Massachusetts / Greater Boston Geography",
            "type": "geography",
            "weight": 8,
            "is_hard_filter": False,
            "config": {
                "target_geographies": ["Massachusetts", "Greater Boston", "Somerville", "MA"],
            },
        },
        {
            "name": "Youth Development Focus",
            "type": "focus_area",
            "weight": 9,
            "is_hard_filter": False,
            "config": {
                "target_focus_areas": [
                    "Youth Development", "Out-of-School Time", "After School",
                    "Youth Programs", "Youth Services",
                ],
            },
        },
        {
            "name": "STEM / STEAM Focus",
            "type": "focus_area",
            "weight": 8,
            "is_hard_filter": False,
            "config": {
                "target_focus_areas": [
                    "STEM", "STEAM", "Robotics", "Coding", "Engineering",
                    "Science", "Technology", "Computer Science",
                ],
            },
        },
        {
            "name": "Workforce Development Focus",
            "type": "focus_area",
            "weight": 7,
            "is_hard_filter": False,
            "config": {
                "target_focus_areas": [
                    "Workforce Development", "Economic Mobility", "Career Readiness",
                    "Job Training", "Internship", "Employment",
                ],
            },
        },
        {
            "name": "Climate / Environmental Focus",
            "type": "focus_area",
            "weight": 7,
            "is_hard_filter": False,
            "config": {
                "target_focus_areas": [
                    "Climate Education", "Environmental Justice", "Clean Energy",
                    "Sustainability", "Climate Tech", "Climate Literacy",
                ],
            },
        },
        {
            "name": "Arts, Culture & Creative Expression",
            "type": "focus_area",
            "weight": 6,
            "is_hard_filter": False,
            "config": {
                "target_focus_areas": [
                    "Arts", "Culture", "Music", "Hip-Hop", "Creative Expression",
                    "Arts & Culture",
                ],
            },
        },
        {
            "name": "Eligibility (501c3 or Fiscal Sponsor)",
            "type": "eligibility",
            "weight": 10,
            "is_hard_filter": True,
            "config": {},
        },
        {
            "name": "Grant Amount Range",
            "type": "amount_range",
            "weight": 5,
            "is_hard_filter": False,
            "config": {
                "min_acceptable": 5000,
                "max_acceptable": 500000,
            },
        },
    ],
)
```

**Note on Eligibility Hard Filter**: The Dojo does NOT yet have its own 501(c)(3) status, but has Teen Empowerment as its primary fiscal sponsor (a 501c3 org). Additional community partners may serve as fiscal sponsors on a per-grant or per-program basis.

The eligibility evaluator (full logic in Task C-P2-04) follows these rules:
- Grant does NOT require 501c3 → **PASS** (open to any org)
- Grant requires 501c3 AND org has its own 501c3 → **PASS**
- Grant requires 501c3 AND allows fiscal sponsorship AND a 501c3 fiscal sponsor is configured for this grant (or org has a default) → **PASS**
- Grant requires 501c3 AND allows fiscal sponsorship AND no fiscal sponsor configured → **PARTIAL (0.5)** — grant can be applied to once a fiscal sponsor is arranged; user is warned
- Grant requires 501c3 AND does NOT allow fiscal sponsorship AND org has no own 501c3 → **HARD FILTER FAILS → score 0.0**

### 9.3 Priority Grant Funders to Pre-Seed

Seed these with `funder_type`, `relationship_notes`, `is_fiscal_sponsor=False`, `is_501c3=True`:

| Funder Name | Type | Tier | Notes |
|-------------|------|------|-------|
| Cummings Foundation | foundation | 1 | MA-based; priority for general operating support |
| MassCEC | government | 1 | MA Clean Energy Center; climate and workforce grants |
| Boston Foundation | foundation | 1 | Greater Boston community grants |
| Barr Foundation | foundation | 1 | Climate, arts, learning |
| United Way of Massachusetts Bay | foundation | 1 | Youth development, economic mobility |
| National Grid Foundation | corporate | 1 | STEM and clean energy |
| Eversource Energy Foundation | corporate | 1 | STEM and community programs |
| Mass Cultural Council | government | 2 | Arts and culture programs |
| Awesome Foundation | foundation | 2 | Small grassroots grants |
| NEFA | foundation | 2 | New England Foundation for the Arts |
| Google.org | corporate | 3 | STEM education, workforce development |
| Microsoft Philanthropies | corporate | 3 | STEM, digital equity |
| Biogen Foundation | corporate | 3 | STEM education |
| Vertex Foundation | corporate | 3 | STEM, workforce |
| Moderna Foundation | corporate | 3 | STEM education and workforce |

### 9.4 Community Partners and Fiscal Sponsors to Pre-Seed

These are the Dojo's organizational partners. Several also serve as fiscal sponsors. Seed with `funder_type="community_partner"`:

| Partner Name | is_fiscal_sponsor | is_501c3 | Notes |
|--------------|-------------------|----------|-------|
| **Teen Empowerment** | **True** | **True** | **PRIMARY default fiscal sponsor for the Dojo** |
| Elizabeth Peabody House | True | True | Can serve as fiscal sponsor for youth/community programs |
| Mystic Learning Center | True | True | Can serve as fiscal sponsor; education focus |
| Groundwork Somerville | True | True | Environmental justice fiscal sponsor for climate programs |
| Better Future Project | True | True | Fiscal sponsor option for climate/environmental grants |
| DLAB | False | False | STEM partner, not a fiscal sponsor |
| SHS Robotics | False | False | STEM partner, not a fiscal sponsor |
| Greentown Labs | False | False | Climate/clean energy partner |
| Somerville Bike Kitchen | False | False | Sustainability partner |
| Haitian Coalition | False | True | Community partner |
| 350 Mass | False | True | Climate advocacy partner |
| Boston Tech Poetics | False | False | Arts/tech partner |
| Community Power Pedal Group | False | False | Community partner |
| SHS Debate | False | False | Youth leadership partner |
| Teen Empowerment | True | True | See above |
| Youth Guidance Boston | False | True | Youth development partner |
| Young Kings Initiative | False | False | Youth leadership partner |
| Youth Artist Incubator | False | False | Arts partner |

**Implementation note**: The fiscal sponsor dropdown in the grant entry form (Task B-P1-06) is populated from `Funder` records where `is_fiscal_sponsor == True`. The dropdown shows the partner name and whether they are a 501c3, so the user can select the most appropriate sponsor for a given grant's requirements.

---

## 10. Default Paragraph Template Specifications

`seed_data.py` must seed these templates into the `templates` table. Each template must have `is_system=True`, `is_active=True`, and appropriate `variables_json`.

### Category: Mission Alignment (2 templates)

**Template 1**: "Mission Alignment — Youth Development"
- Body: `"{{org_name}} is a youth-centered community program based in {{city}}, {{state}}, serving {{target_population}}. Our mission is {{mission}} We believe that every young person deserves access to safe, structured, and affirming spaces that nurture their potential and connect them to real-world pathways."`
- Variables: `["org_name", "city", "state", "target_population", "mission"]`
- Word count target: 75

**Template 2**: "Mission Alignment — Equity & Access"
- Body: `"{{org_name}} centers equity and multicultural inclusion in all of our programming. We serve {{target_population}} in {{city}}, with particular focus on low-income youth, first-generation students, multilingual households, and youth underrepresented in STEM and career pathways. Our approach is youth-led, community-rooted, and grounded in the lived experiences of the young people we serve."`
- Variables: `["org_name", "target_population", "city"]`
- Word count target: 80

### Category: Need Statement (2 templates)

**Template 3**: "Need Statement — Somerville Youth"
- Body: `"In {{city}}, over 4,900 students are enrolled in public schools, with more than 40% considered economically disadvantaged. Over 50 languages are spoken in Somerville schools, reflecting a richly diverse but often under-resourced population. Youth in our community face significant challenges: limited access to structured out-of-school programming, gaps in STEM exposure, mental health pressures, and limited career awareness. {{org_name}} was created to directly address these gaps."`
- Variables: `["city", "org_name"]`

**Template 4**: "Need Statement — STEM Access Gap"
- Body: `"Young people in underserved Greater Boston communities face persistent barriers to STEM education and career exposure. Without structured access to robotics, coding, and engineering experiences in their youth, these students are systematically excluded from the fastest-growing sectors of the economy. {{org_name}} is closing this gap through hands-on STEM programming, peer mentorship, and direct connections to local STEM employers."`
- Variables: `["org_name"]`

### Category: Population Served (1 template)

**Template 5**: "Population Served"
- Body: `"{{org_name}} serves {{target_population}} in {{city}} and Greater Boston, with a primary focus on low-income youth, first-generation students, multilingual learners, and youth seeking mentorship and career exposure. We prioritize young people who face structural barriers to academic and economic success, and we actively recruit and retain youth from historically underrepresented communities in STEM, clean energy, and the creative economy."`
- Variables: `["org_name", "target_population", "city"]`

### Category: Program Description (3 templates — one per major program)

**Template 6**: "Program Description — STEM Explorers"
- Body: `"{{org_name}}'s STEM Explorers program engages {{target_population}} in hands-on robotics, coding, engineering challenges, and maker projects. Through partnerships with DLAB, SHS Robotics, and local universities, participants gain real-world STEM skills, exposure to STEM careers, and mentorship from professionals in the field. Youth complete structured projects and are connected to STEM internship and scholarship opportunities."`
- Variables: `["org_name", "target_population"]`

**Template 7**: "Program Description — Climate Leaders Academy"
- Body: `"{{org_name}}'s Climate Leaders Academy equips {{target_population}} with climate literacy, environmental justice education, and hands-on sustainability projects. In partnership with the Better Future Project, Greentown Labs, and the Somerville Bike Kitchen, youth learn about clean energy careers, conduct community action projects, and develop the knowledge and skills to be climate advocates in their communities."`
- Variables: `["org_name", "target_population"]`

**Template 8**: "Program Description — Workforce Ready"
- Body: `"{{org_name}}'s Workforce Ready program prepares {{target_population}} for the job market through resume building, mock interviews, career exploration, and job readiness workshops. Youth receive stipends for participation, are matched with mentors from local industries, and are connected to internship opportunities with partner employers. This program directly addresses career awareness gaps and supports economic mobility for Greater Boston youth."`
- Variables: `["org_name", "target_population"]`

### Category: Evaluation Plan (1 template)

**Template 9**: "Evaluation Plan"
- Body: `"{{org_name}} tracks program outcomes through a combination of attendance tracking, participant surveys, and goal-attainment records. Key metrics include: youth enrolled and retained, STEM workshops completed, career workshops attended, mentorship matches made, internship placements secured, and self-reported measures of confidence, belonging, and career awareness. Data is collected at program entry, mid-year, and program exit, and reviewed quarterly by program staff."`
- Variables: `["org_name"]`

### Category: Budget Narrative (1 template)

**Template 10**: "Budget Narrative"
- Body: `"The requested funds from {{funder_name}} will support {{program_name}} at {{org_name}}. Funds will be used for: personnel (program staff and youth stipends), program supplies and materials, workshop facilitation costs, field trip and event expenses, and a portion of operational overhead. All expenditures will be tracked and reported per the funder's requirements, with full financial records available upon request."`
- Variables: `["funder_name", "program_name", "org_name"]`

### Category: Sustainability Plan (1 template)

**Template 11**: "Sustainability Plan"
- Body: `"{{org_name}} is committed to the long-term sustainability of {{program_name}}. We are actively pursuing a diversified funding base including: foundation grants, government funding, individual donors, earned revenue from workshops and events, and in-kind partnerships. We are also pursuing our 501(c)(3) designation, which will expand our eligibility for a wider range of grant funding. Current partnerships with {{partner_names}} provide in-kind resources that reduce program costs."`
- Variables: `["org_name", "program_name", "partner_names"]`

### Category: Organization Capacity (1 template)

**Template 12**: "Organization Capacity"
- Body: `"{{org_name}} has demonstrated the ability to deliver high-quality, consistent programming for {{target_population}} in {{city}}. Our team brings expertise in youth development, STEM education, workforce readiness, and community organizing. We maintain strong partnerships with {{partner_names}}, which provide additional capacity, expertise, and resources. Our organizational infrastructure includes established record-keeping, participant tracking systems, and a track record of responsible financial management."`
- Variables: `["org_name", "target_population", "city", "partner_names"]`

### Category: Youth Voice (1 template)

**Template 13**: "Youth Voice & Leadership"
- Body: `"Youth voice is central to {{org_name}}'s program design. Young people are not simply recipients of our programming — they are co-designers, peer leaders, and advocates. Youth participate in program planning, provide feedback on curriculum, serve as near-peer mentors, and are compensated for leadership roles through our stipend program. This approach ensures that programming remains relevant, engaging, and responsive to the actual needs and interests of the communities we serve."`
- Variables: `["org_name"]`

### Category: Partnerships (1 template)

**Template 14**: "Community Partnerships"
- Body: `"{{org_name}} has built a robust network of community partners who contribute expertise, resources, and opportunities to our youth. Current partners include: Better Future Project (climate education), Greentown Labs (clean energy career exposure), DLAB (STEM and robotics), SHS Robotics (peer robotics mentorship), Elizabeth Peabody House (community services), Teen Empowerment (youth leadership), and Somerville Bike Kitchen (sustainability and community engagement). These partnerships amplify our reach and deepen the quality of youth experiences."`
- Variables: `["org_name"]`

---

## 11. Default Review Checklist Item Specifications

`src/templates/checklists/default_checklist_items.py` must define these items. They are seeded by `ReviewService.initialize_checklists()` when a new review is created.

### Review 1 — Fact Verification (6 items)

| Item | is_critical |
|------|-------------|
| Every statistic cited has a named source document in the org library or a publicly verifiable source | True |
| All program names match exactly those in the organization profile | True |
| All dates, capacities, and participant counts are verifiable against org documents | True |
| No program outcomes are claimed that are not documented in the org profile or past reports | True |
| All geographic references are accurate (city, region, service area) | False |
| No staff titles, bios, or credentials are misrepresented | False |

### Review 2 — Assumption Log

This review type uses free-form `AssumptionRecord` entries rather than pre-defined checklist items. The checklist is marked COMPLETED when the reviewer confirms they have logged all assumptions. Seed one item:

| Item | is_critical |
|------|-------------|
| I have reviewed the entire draft and logged every assumption made in the form below | True |

### Review 3 — Ambiguity Resolution Record

Same pattern as Review 2 — free-form `AmbiguityRecord` entries. Seed one item:

| Item | is_critical |
|------|-------------|
| I have reviewed the grant instructions and logged every ambiguity encountered and how it was resolved | True |

### Review 4 — Compliance Checklist (8 items)

| Item | is_critical |
|------|-------------|
| All required narrative sections are completed | True |
| Word or character limits are respected for each section | True |
| All required attachments are prepared and listed in the document requirements checklist | True |
| Budget format matches the funder's stated requirements | True |
| The application is submitted by the correct entity (org or fiscal sponsor, as required) | True |
| All funder-specific questions are answered in full | True |
| No prohibited content is included (per any funder-stated restrictions) | False |
| Content is aligned with the Dojo's legal, ethical, and organizational policies | True |

---

## 12. Integration Checkpoints

### Checkpoint 1 — After Phase 0 + Track A Phase 1 Complete
- Database initializes: `alembic upgrade head` succeeds
- Seed runs: `python src/db/seed_data.py` inserts org, criteria, funders without error
- Track B and Track C can both start (B uses model stubs; C uses actual models)

### Checkpoint 2 — After Track C Phase 2 Complete
- Scoring engine unit tests pass (100% coverage on scoring_engine.py)
- `GrantService.create_grant()` can be called from Track B pages
- Track D unit tests for Phase 2 modules pass

### Checkpoint 3 — After Phase 4 Complete (Application Management)
- Full path: create grant → create application → create draft → view manifest works end-to-end
- Track D integration test `test_full_grant_lifecycle.py` passes through draft creation step

### Final Checkpoint — After Phase 6 Complete
- End-to-end happy path passes: enter grant → score → approve to apply → draft → complete 4 reviews → approve → record submission
- Hard gate test: `SubmissionBlockedError` raised for all non-compliant scenarios
- `pytest tests/` passes with ≥ 80% coverage on all service and engine modules
- `streamlit run src/app/main.py` launches and all 8 pages render without errors
- Weekly report generates with all 5 sections and correct grant ranking

---

## 13. Critical Implementation Rules

These rules are non-negotiable and must be enforced by agents in code, not just UI:

1. **Hard Gate**: `approve_application()` must check all 4 checklists at the SERVICE LAYER. The UI approval button is a secondary check only.
2. **No Raw SQL**: SQLAlchemy ORM exclusively. No `text()` queries for user-supplied data.
3. **No Anthropic SDK**: `requirements.txt` must not include `anthropic`. The production system does not call any paid AI API.
4. **Soft Delete Only**: No `DELETE` statements on grant or application records. `is_deleted = True` only.
5. **Deterministic Scoring**: `score_grant()` must be a pure function — same inputs always produce same outputs. No randomness, no timestamps in score calculation.
6. **Scoring Audit Trail**: Every scored grant must have `score_breakdown_json` stored in the database.
7. **File Versioning**: Never overwrite any file. Include version and datetime headers in all generated files.

---

## 14. Success Criteria

### Functional
- [ ] Grants are entered, auto-scored by rules engine, and displayed with fit score and urgency badge
- [ ] The eligibility hard filter correctly scores 0.0 for grants the Dojo cannot apply to (requires 501c3, no fiscal sponsor)
- [ ] All four review checklists are completable with per-item tracking
- [ ] No application can advance to APPROVED without all 4 checklists complete and no blocking items — enforced at service layer
- [ ] Weekly report generates with all 5 sections from live DB data
- [ ] System runs with `streamlit run src/app/main.py` after `alembic upgrade head` + `seed_data.py`

### Technical
- [ ] `pytest tests/` passes with ≥ 80% coverage on service and engine modules
- [ ] Hard gate `SubmissionBlockedError` raised for all non-compliant scenarios in tests
- [ ] `requirements.txt` contains no `anthropic` package
- [ ] Scoring engine is deterministic: `score_grant()` returns identical results for identical inputs
- [ ] All models have `created_at`, `updated_at`, `is_deleted` columns
- [ ] Alembic migrations apply cleanly from `alembic upgrade head`

---

## 15. Change Log

### Version 1.2.0 — 2026-06-23
- **Fiscal sponsor model added**: Funder table gains `is_fiscal_sponsor` and `is_501c3` flags
- **Per-grant fiscal sponsor**: Grant model gains optional `fiscal_sponsor_id FK → funders`
- **Scoring engine updated**: Eligibility evaluator uses per-grant sponsor with PASS / PARTIAL / FAIL tiers
- **Grant entry form updated**: Fiscal sponsor dropdown appears when grant requires 501c3
- **Section 9.4 added**: Community partners and fiscal sponsors pre-seed table; Teen Empowerment = primary default
- **Loader architecture**: `seed_data.py` redesigned as a loader; org data lives in `data/org_profile/org_profile_seed_data.md`; `org_profile_loader.py` added; supports `--profile` arg for multi-org use

### Version 1.1.0 — 2026-06-23
- Initial implementation plan created from SDLC v1.1.0 specifications
- Scope: Phases 1–6 only (Ollama Phase 7 and Docker Phase 8 deferred)
- Seed data from Org_Context/Seed_Data.docx (The Dojo at Somernova, confirmed)
- 14 default paragraph templates specified (Section 10)
- Default checklist items specified for all 4 review types (Section 11)
- Agent fidelity set to "detailed guidance" (not strict contract)
- File versioning convention established: no overwrites, datetime + semver headers required

---

**Document**: 04_Implementation_Plan_v1.1.0.md
**Owner**: Grants_Assistant Project
**Next Step**: Owner review and approval → Agent team execution