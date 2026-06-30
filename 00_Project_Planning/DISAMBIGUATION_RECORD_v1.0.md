---
title: GMAS v1.1.0 — Agent Disambiguation Record
version: 1.0.0
created: 2026-06-25
modified: 2026-06-25
status: Living document — updated as implementation proceeds
---

# GMAS v1.1.0 — Agent Disambiguation Record

This document records every decision made by the implementation agent where the
specification was ambiguous, silent, or required a judgment call. Per project
instructions: document the alternative chosen, the assumption made, and the
rationale.

---

## D-001 — environment.yml Added (Not in Spec)

**Spec gap**: The Implementation Plan (IP) specifies `requirements.txt` and
`pyproject.toml` but does not mention `environment.yml`.

**Decision**: Created `environment.yml` alongside `requirements.txt`.

**Assumption**: User memory explicitly requires conda for all Python runtime work
(permanent memory: `feedback_conda.md`). A conda project always ships an
`environment.yml` so teammates can reproduce the exact environment with
`conda env create -f environment.yml && conda activate gmas`.

**Alternative not chosen**: venv + requirements.txt only.

---

## D-002 — weasyprint Windows Compatibility

**Spec gap**: The IP includes `weasyprint>=62.0` in requirements.txt without noting
its native dependency requirements on Windows (GTK/Cairo runtime).

**Decision**: Included `weasyprint` in both `requirements.txt` and `environment.yml`
(via conda-forge channel in environment.yml, which handles native deps automatically).
Added a comment in `requirements.txt` explaining the Windows caveat.

**Assumption**: User is on Windows 11 (confirmed by environment). weasyprint via
conda-forge is the recommended Windows install path. If PDF export fails, the
Markdown export path remains fully functional.

---

## D-003 — Alembic init via Manual File Creation

**Spec gap**: Task A-P0-07 says `alembic init src/db/migrations`. This is a CLI
command that requires alembic installed in the active conda environment.

**Decision**: Created all Alembic files manually rather than running `alembic init`:
- `alembic.ini` at project root
- `src/db/migrations/env.py` (configured with GMAS-specific imports)
- `src/db/migrations/script.py.mako` (standard Alembic template)
- `src/db/migrations/versions/` directory

**Assumption**: At code generation time, the conda env does not yet exist (chicken-and-egg).
Manual creation is functionally identical to `alembic init`. The user runs
`conda env create -f environment.yml && conda activate gmas && alembic upgrade head`
to initialize the schema.

---

## D-004 — UUID Primary Keys

**Spec gap**: The IP references `UUID FK → funders` for the fiscal sponsor but does
not explicitly specify whether all PKs are UUID or integer.

**Decision**: All model PKs are `UUID` (stored as `CHAR(36)` in SQLite, native UUID
in PostgreSQL). Default: `uuid.uuid4`.

**Assumption**: UUID PKs are standard for multi-org, potentially cloud-migrated
systems. They also avoid sequential ID guessing. The HLD mentions UUID in the
fiscal_sponsor_id FK, implying UUID is the intent throughout.

---

## D-005 — Grant Status VALID_TRANSITIONS (Full State Machine)

**Spec gap**: The IP shows VALID_TRANSITIONS is in `grant.py` and the state machine
enforces it, but never lists the complete set of valid transitions.

**Decision**: Defined the following transitions (inferred from the grant lifecycle
described across PRD, HLD, and task specs):

```python
VALID_TRANSITIONS = {
    "DISCOVERED":        ["EVALUATED", "DEFERRED", "ARCHIVED"],
    "EVALUATED":         ["RECOMMENDED", "DEFERRED", "ARCHIVED"],
    "RECOMMENDED":       ["APPROVED_TO_APPLY", "DEFERRED", "ARCHIVED"],
    "APPROVED_TO_APPLY": ["SUBMITTED", "WITHDRAWN", "ARCHIVED"],
    "DEFERRED":          ["DISCOVERED", "EVALUATED", "RECOMMENDED", "ARCHIVED"],
    "SUBMITTED":         ["AWARDED", "DECLINED", "WITHDRAWN"],
    "AWARDED":           ["ARCHIVED"],
    "DECLINED":          ["ARCHIVED"],
    "WITHDRAWN":         ["ARCHIVED"],
    "ARCHIVED":          [],
}
```

**Assumption**: DEFERRED is a "parking lot" state that can be re-activated to any
earlier state. Terminal states (AWARDED, DECLINED, WITHDRAWN) can only be ARCHIVED.
ARCHIVED is always a terminal state.

---

## D-006 — Application Status State Machine

**Spec gap**: Application statuses are referenced throughout the plan but the valid
transitions are never listed.

**Decision**:
```python
VALID_APP_TRANSITIONS = {
    "DRAFT":       ["IN_REVIEW", "WITHDRAWN"],
    "IN_REVIEW":   ["DRAFT", "APPROVED", "WITHDRAWN"],
    "APPROVED":    ["SUBMITTED", "WITHDRAWN"],
    "SUBMITTED":   ["AWARDED", "DECLINED", "WITHDRAWN"],
    "AWARDED":     [],
    "DECLINED":    [],
    "WITHDRAWN":   [],
}
```

**Assumption**: Applications can be pushed back to DRAFT from IN_REVIEW (reviewer
requests changes). APPROVED → SUBMITTED on record_submission(). Outcomes are terminal.

---

## D-007 — ScoreResult and CriterionResult Data Structures

**Spec gap**: Task C-P2-04 says "ScoreResult and CriterionResult dataclasses" but
does not define their fields.

**Decision**:
```python
@dataclass
class CriterionResult:
    name: str
    evaluator_type: str    # "geography", "focus_area", "eligibility", "amount_range"
    raw_score: float       # 0.0 – 1.0 before weighting
    weight: int            # criterion weight from criteria_json
    weighted_score: float  # raw_score * weight
    passed: bool           # False = hard filter failed
    notes: str             # human-readable explanation

@dataclass
class ScoreResult:
    fit_score: float                      # 0.0 – 10.0 normalized
    hard_filter_failed: bool
    criterion_results: list[CriterionResult]
    score_breakdown_json: dict            # serializable form stored in DB
```

**Assumption**: `fit_score` is `sum(weighted_scores) / max_possible * 10` when
no hard filter fails. Score 0.0 when hard_filter_failed=True.

---

## D-008 — String Column Lengths (SQLite permissive, explicit for PostgreSQL readiness)

**Spec gap**: No column length constraints are specified in the IP.

**Decision**: Applied consistent defaults:
- Short identifier / name: `String(255)`
- URL / path: `String(1000)`
- Medium text (single paragraph): `Text` (unbounded)
- JSON stored as text: `Text`

**Assumption**: These sizes support PostgreSQL migration (Phase 3+) without migration
changes. SQLite ignores VARCHAR length anyway.

---

## D-009 — thefuzz Added for Deduplication

**Spec gap**: Task C-P2-02 describes fuzzy string matching with "0.85 similarity"
threshold but does not specify the library.

**Decision**: Added `thefuzz>=0.22.0` and `python-Levenshtein>=0.25.0` to
requirements.txt. Used `thefuzz.fuzz.token_set_ratio()` for name comparison.

**Assumption**: `thefuzz` is the standard Python library for fuzzy string matching
(wraps Levenshtein distance). `token_set_ratio` is robust to word order differences
in grant names. `python-Levenshtein` provides C-speed backend.

---

## D-010 — All Models Created in Phase 1 (Not Spread Across Phases)

**Spec gap**: Phase 4 models (Application, Draft, Review, Manifest, Template, Report)
are defined as "Phase 4 Tasks" but must exist for Alembic to generate a consistent
initial schema.

**Decision**: All models are created during Phase 1 code generation. Migration 001
creates all tables. This matches the milestone ("alembic upgrade head completes
without error") and avoids a split schema where Phase 1 tables exist but Phase 4
tables are missing from the DB.

**Assumption**: Generating all models upfront is strictly correct — phases reflect
FEATURE development order, not model creation order. This is consistent with
`src/models/__init__.py` importing all models for Alembic.

---

## D-011 — org_document.py Created in Phase 1 (Listed in Directory, Not in Task Specs)

**Spec gap**: `src/models/org_document.py` appears in the directory structure (Section 5)
and is referenced in `src/models/__init__.py` but has no dedicated task spec.

**Decision**: Created alongside Phase 1 models. OrgDocument is referenced in the
Organization model's relationship and in the Document Requirements checklist.

**Assumption**: OrgDocument stores uploaded supporting documents (990s, letters of
support, etc.). Fields: id, org_id (FK), filename, file_path, doc_type, uploaded_at.

---

## D-012 — Paragraph Template Count: 14 Templates Seeded (Not Exactly 15+)

**Spec gap**: Task A-P4-08 says "15+ paragraph templates". Section 10 defines exactly
14 named templates (Templates 1–14, noting Template 14 is "Community Partnerships").

**Decision**: Seed all 14 explicitly-specified templates. Do not invent additional
templates that aren't in the spec.

**Assumption**: "15+" in the task spec was a planning estimate; Section 10 is the
authoritative content spec. The system allows users to add more templates via the UI.

---

## D-013 — Teen Empowerment Listed Twice in Section 9.4

**Spec gap**: Section 9.4 of the IP lists "Teen Empowerment" twice in the community
partners table (rows 1 and 15).

**Decision**: Insert Teen Empowerment once. The seed_data.py idempotency check
(by org name) naturally prevents duplicates.

**Assumption**: This was a copy-paste artifact in the spec. There is only one Teen
Empowerment organization.

---

## D-014 — DocumentRequirement Model Added Post-Migration (Plan Spec A-P4-01)

**Phase:** Phase 2-6 Services (session 2)
**Decision:** Implementation Plan A-P4-01 specified `Application, DocumentRequirement`
in `src/models/application.py`, but the Phase 1 model generation missed
`DocumentRequirement`. It was added during Phase 2-6 service writing.

**Resolution:** Added `DocumentRequirement` ORM class to `src/models/application.py`,
added the `document_requirements` table to migration `002_application_models.py`
(appended at the end of the upgrade function, before downgrade), and updated
`src/models/__init__.py` to export it. No new migration version was needed since
002 had not yet been run against any deployed database.

**Risk:** If 002 had already been applied to an existing DB, this would require
migration 003. Acceptable in pre-launch context.

**Assumptions:**
- `document_requirements.ondelete = "CASCADE"` (application delete cascades)
- Default document requirements list is hard-coded in `application_service.py`
  (7 standard documents); user can add custom requirements via the Documents tab
- `is_required=True` for all defaults; `is_complete=False` until user marks complete

---

## D-015 — Settings `export_dir` Field Added to Config (Not in Original Plan)

**Phase:** Phase 2-6 Services / UI
**Decision:** `src/app/pages/05_reports.py` and `src/services/report_service.py` both
reference `settings.export_dir`. This field was absent from the original Settings class.

**Resolution:** Added `export_dir: str = "data/exports"` to `src/utils/config.py`.
This matches the existing `data/exports/` directory created in Phase 0 scaffolding.
Fully overridable via the `EXPORT_DIR` environment variable.

---

## D-016 — Grant Discovery Subsystem: Aggregator ToS Compliance (v1.2.0)

**Phase:** v1.2.0 Discovery feature (new scope, post-v1.1.0)
**Decision:** User requested "search then scrape" across sources and explicitly
selected **Instrumentl** and **Candid** aggregators. Both prohibit automated
scraping in their Terms of Service.

**Resolution:** Built the *compliant* path instead of a scraper:
- **Candid** → official API connector (`CandidApiSource`), key-gated and
  **disabled by default** (mirrors the Ollama/Google Docs deferred-integration
  pattern). Activates only when `candid_api_enabled=True` and a key is set.
- **Instrumentl** → no scraping. `InstrumentlCsvImporter` parses the CSV/Excel
  export that Instrumentl subscribers are permitted to download from their own
  account. ToS-compliant.
- `WebSearchSource` hard-blocks `instrumentl.com`, `candid.org`, and
  `foundationcenter.org` domains from auto-fetch even if they appear in results.

**Assumptions:**
- The user (or The Dojo) does not currently hold a paid Candid API key — connector
  ships off.
- Fetching a *funder's own public grant page* for the org's own application
  research is legitimate and not equivalent to aggregator scraping.

## D-017 — No-AI Extraction via Deterministic Rules + Human Confirm (v1.2.0)

**Decision:** "Scrape the data needed for the application" normally implies LLM
field extraction, but production GMAS forbids paid AI APIs (core constraint).

**Resolution:** `src/discovery/extractor.py` is fully deterministic (regex/HTML
rules) — same input always yields the same output. Every extracted field carries
a 0.0–1.0 confidence and the evidence snippet it came from. Nothing auto-creates
a Grant: candidates are staged in `discovered_candidates` (status NEW) and only
become Grants when a human confirms via the Discover → Review form. This preserves
GMAS's existing human-in-the-loop philosophy. Local Ollama (deferred Phase 7)
remains the future option for smarter extraction without a paid API.

**Assumptions:**
- Rules-based extraction is intentionally conservative; low-confidence fields are
  flagged (🔴/🟡) for the human rather than trusted.
- The polite fetcher honors robots.txt by default (`discovery_respect_robots=True`),
  sets a descriptive User-Agent, rate-limits per host, and caches to disk.

## D-018 — Pre-existing v1.1.0 Unit Tests Found Broken (Documented, Not Fixed Here)

**Decision:** Running the full suite under the new conda env revealed that several
original v1.1.0 unit tests (`test_scoring_engine.py`, `test_template_renderer.py`,
parts of `test_application_service.py`) were authored without ever being executed
(no env existed at build time) and assert against an imagined API — e.g. they
expect a `criteria_results` JSON key while the engine emits `criteria`, and use
`Model.__new__(Model)` which bypasses SQLAlchemy instrumentation.

**Resolution:** Left these pre-existing test files **unchanged** to keep the
v1.2.0 discovery commit cleanly scoped. The application code itself (scoring
engine, template renderer) produces correct output; only the *tests* are stale.
Flagged for a dedicated follow-up pass to repair the v1.1.0 test suite.

**Risk:** The original test suite does not currently pass end-to-end. The new
discovery tests (`test_extractor.py`, `test_aggregator_csv.py`) do pass.

**RESOLVED (follow-up, 2026-06-30):** The full suite now passes (127 tests). Fixes:
- `test_scoring_engine.py` rewritten to use duck-typed `SimpleNamespace` stand-ins
  and the engine's real criteria `config` schema, `is_hard_filter` flag, and
  `criteria` JSON key.
- `test_template_renderer.py` fixtures use the real `Organization(...)` constructor
  instead of `__new__`.
- **Genuine product bug fixed** in `build_org_context`: nullable columns (e.g.
  `values_text`) returned `None`, which would render literal "None" in templates —
  now coerced to "".
- **Genuine product bug fixed** in `ApplicationService.approve_application`: it
  attempted `DRAFT → APPROVED`, which the state machine forbids. The approval flow
  was unrunnable end-to-end. Now advances `DRAFT → IN_REVIEW → APPROVED` when
  reviews are complete. (Caught by both the unit test and the full-lifecycle
  integration test.)
- `test_report_generation.py` used near-identical grant titles from one funder,
  which the dedup engine correctly flagged as duplicates — titles made distinct.

---

## D-019 — "Search Everywhere" Breadth Strategy (v1.2.0)

**Decision:** User clarified discovery must "search everywhere," not run a single
query. Needed a strategy to broaden coverage without a paid search API.

**Resolution:** Added `run_full_sweep()` combining three breadth mechanisms:
1. **Query expansion** (`query_expander.py`) — generates up to 40 deterministic
   queries from the org profile (each focus area × geography scope {city, state,
   New England, national} × population × this year + next).
2. **Funder-wide site sweep** — fetches the website of *every* funder in the DB
   (the 15 priority funders + 17 community partners already seeded), probing
   common grant sub-paths (/grants, /apply, …) off each homepage.
3. **Curated public portals** — Mass.gov, Boston.gov, Somerville, Barr
   Foundation, The Boston Foundation, etc., swept every run.

Exposed via the Discover page "🌐 Search Everywhere" button and the scheduled
scan `--sweep` flag.

**Assumptions:**
- Breadth is capped (≤40 queries, polite per-host rate limiting + caching) so a
  full sweep stays in the minutes range, suitable for a weekly scheduled run.
- Sub-path probing only fires off bare homepages to stay courteous.
- All fetches still honor robots.txt and the ToS-domain blocklist from D-016.

---

*This record is maintained by the implementation agent and should be reviewed by
the project owner before Phase 6 integration testing.*
