---
title: GrantNova — Grant Scout Module Task Implementation Plan
version: 1.0.0
created: 2026-07-16
modified: 2026-07-16
status: DRAFT — awaiting owner confirmation before execution
system: GrantNova (formerly GMAS)
module: Grant Scout
orchestration: Multi-agent team, orchestrator-verified
---

# GrantNova — Grant Scout Module: Task Implementation Plan (TIP)

## 0. How to read this document

This is an **execution plan for a multi-agent team**. It is organized into **Work
Packages (WP)**. Each WP has:

- an **objective**, the **files** it owns, and its **dependencies**;
- a list of **tasks**;
- explicit, testable **Acceptance Criteria (AC)** — each AC ends in a runnable
  **VERIFY** command that produces observable output.

**Orchestrator rule (non-negotiable):** a task is "done" ONLY when the orchestrator
personally re-runs its VERIFY command and sees the stated output. Subagent claims of
completion are never accepted on trust. This is the whole point of the AC/VERIFY
format — it makes correctness checkable rather than asserted.

**Environment for every VERIFY command:** the `gmas` conda env
(`C:\Users\jhenn\.conda\envs\gmas\python.exe`). Baseline before any work: **127 tests
passing.** No WP may reduce that number; each feature WP raises it.

---

## 1. Context & current state (verified 2026-07-16)

GrantNova (the system formerly nicknamed GMAS) already contains an embryonic Scout as
the committed `src/discovery/` subsystem (v1.2.0). Verified by reading every file and
running the suite:

| Scout phase | Status | Implemented in | Test coverage |
|---|---|---|---|
| **HUNT** (find) | ✅ built | `query_expander.py`, `sources/grants_gov.py`, `sources/web_search.py`, `sources/funder_site.py`, `DiscoveryService.run_full_sweep()` | expander only |
| **GATHER** (collect) | ✅ built | `fetcher.py` (robots + rate-limit + cache), `extractor.py` (deterministic + confidence + evidence), `DiscoveredCandidate` staging | extractor, aggregator CSV only |
| **EVALUATE** (assess fit) | ⚠️ shallow | dedup flag on stage; fit/eligibility computed only **after** human import via `GrantService` | none |
| **REPORT** (brief the user) | ❌ missing | — (only a pasted note in the uncommitted PRD diff) | none |

**Confirmed gaps this plan closes:**
1. EVALUATE happens too late — the review queue is unranked and unscored.
2. REPORT does not exist.
3. `discovery_service.py`, `fetcher.py`, and all three live sources have **zero tests** —
   the largest correctness risk.
4. No formal `FR-SCOUT` requirements in the SDLC docs.
5. The system is still named "GMAS" in 99 places across 40 files.

## 2. Locked decisions (owner, 2026-07-16)

| # | Decision | Consequence for this plan |
|---|---|---|
| D-A | **Scope = docs + full build** | Both SDLC formalization (WP-6) and code implementation (WP-2..5) are in scope; all verified by orchestrator. |
| D-B | **System renamed to "GrantNova"** | WP-1 renames GMAS→GrantNova everywhere; module is "Grant Scout" within GrantNova. |
| D-C | **Pre-review scoring + ranked queue, GREEN flags** | Candidates are scored + eligibility-checked at stage time; queue is ranked best-first. Strong eligible matches are highlighted **green (🟢)**. Weak/ineligible ones are quietly deprioritized/filtered — **no alarmist red** at the queue level. (Field-level confidence flags in the import form keep their existing 🟢/🟡/🔴 meaning — that is a different, already-shipped indicator.) |
| D-D | **Build the REPORT phase now** | WP-5 implements the Scout intelligence digest. |

## 3. Naming conventions introduced by this plan

- **System / product name:** `GrantNova` (replaces `GMAS` and the expansion
  "Grants Manager Assistant System").
- **Module name:** `Grant Scout` (user-facing), `scout` (code/namespace where new).
- **Requirement IDs:** `FR-SCOUT-NNN` (functional), `NFR-SCOUT-NNN` (non-functional),
  grouped by Hunt / Gather / Evaluate / Report — matching the existing `FR-XXX-NNN`
  convention in the PRD (§2).
- **Acceptance-criteria IDs:** `AC-SCOUT-<AREA>-NN`.
- **Disambiguation IDs:** continue the existing sequence from `D-020`.
- **The DB table stays `discovered_candidates`.** The SQLite file is **renamed
  `data/gmas.db` → `data/grantnova.db`** and, in the process, brought under Alembic
  control (it currently is not — see §3.1) via a backup → Alembic-rebuild → data-copy
  procedure (WP-1 §DB, decision D-020).

### 3.1 Critical finding: the live DB is not under Alembic control

Verified 2026-07-16: `init_db()` creates the schema with
`Base.metadata.create_all()`, **not** Alembic. Consequences on the live `data/gmas.db`
(created 2026-06-25, holding real seed data — 32 funders, 14 templates, 1 org, 1
criteria set):

- There is **no `alembic_version` table** — the DB is unversioned.
- It **predates migration 003**, so it has **no `discovered_candidates` table**. The
  discovery/Scout feature has never actually had a home in the real database; only the
  in-memory test DBs (built fresh from models) exercise it.
- `create_all()` (models) and the Alembic migration chain are **two sources of truth
  for the schema, and they have already drifted.**

This plan makes **Alembic the authoritative schema source** for the real database and
uses the rename as the occasion to reconcile the drift (NFR-SCOUT-006). Because the
Jun-25 `create_all` schema may not byte-match the migration DDL (commit `4f373b7` edited
migration 001 *after* the live DB existed), we do **not** `alembic stamp` the old file
in place; we **rebuild a canonical schema from the full migration chain and copy the
data across** — the safer, drift-proof path.

---

## 4. Functional & non-functional requirements (with acceptance criteria)

These are the requirements WP-6 will fold into the PRD/HLD/DD and that the code WPs
must satisfy. Each maps to the WP that implements it.

### 4.1 HUNT — `FR-SCOUT-1xx`  (owned by WP-3 hardening; already built)

- **FR-SCOUT-101** — Scout shall discover opportunities from grants.gov (official
  API), web search (keyless DuckDuckGo default, pluggable), and known funder sites +
  curated public portals.
- **FR-SCOUT-102** — Scout shall expand the org profile into a deterministic battery of
  ≤40 queries (focus × geography × population × year) for a "search everywhere" sweep.
- **FR-SCOUT-103** — All discovery shall be safe with any source disabled (returns
  empty; never raises).

### 4.2 GATHER — `FR-SCOUT-2xx`  (owned by WP-3 hardening; already built)

- **FR-SCOUT-201** — Fetching shall honor robots.txt (default on), send a descriptive
  User-Agent, rate-limit per host, and cache responses to disk.
- **FR-SCOUT-202** — Field extraction shall be fully deterministic (no AI); identical
  input yields identical output.
- **FR-SCOUT-203** — Every extracted field shall carry a 0.0–1.0 confidence and an
  evidence snippet.
- **FR-SCOUT-204** — ToS-restricted aggregator domains (instrumentl.com, candid.org,
  foundationcenter.org) shall never be auto-fetched; Candid via official API only,
  Instrumentl via user-supplied CSV only.

### 4.3 EVALUATE — `FR-SCOUT-3xx`  (owned by WP-4)

- **FR-SCOUT-301** — When a candidate is staged, Scout shall compute a fit score
  (0.0–10.0) using the **active selection-criteria rule set** (reusing the existing
  `scoring_engine`), without importing it as a Grant.
- **FR-SCOUT-302** — Scout shall compute an `eligibility_status` of `ELIGIBLE`,
  `INELIGIBLE`, or `UNKNOWN` by applying the criteria's hard filters (e.g. 501(c)(3)
  requirement vs. org profile, geography). **Fiscal-sponsorship rule (community-org
  critical):** when a grant requires 501(c)(3) BUT the candidate's
  `fiscal_sponsorship_allowed` is true AND the org profile uses/permits a fiscal
  sponsor, the status is `ELIGIBLE`, not `INELIGIBLE`. When the active org has no
  selection-criteria set, evaluation returns `UNKNOWN` and fit `0.0` rather than
  raising.
- **FR-SCOUT-303** — `list_candidates()` shall return NEW candidates **ranked by fit
  score descending**, with eligible candidates ahead of ineligible ones at equal score.
- **FR-SCOUT-304** — Candidates with fit score ≥ `recommendation_threshold` (7.0) AND
  `ELIGIBLE` shall be marked `is_strong_match = True` and surfaced with a **green**
  indicator (🟢) in the queue. Ineligible/weak candidates are deprioritized and
  hideable via a toggle — never red-flagged at queue level.
- **FR-SCOUT-305** — Re-evaluation shall be idempotent and re-runnable when the active
  criteria set changes (`reevaluate_candidates()`), without duplicating rows.
- **FR-SCOUT-306** (deadline-aware, community-org critical) — Scout shall classify each
  candidate's deadline urgency by reusing `engine/deadline_classifier.py` (RED ≤30d /
  YELLOW 31–60d / GREEN 61–90d / GRAY >90d or rolling). An **"Act Now"** flag is set
  when a candidate is `ELIGIBLE`, `is_strong_match`, AND urgency is RED/YELLOW. Rolling
  (no-deadline) opportunities are treated as low-pressure standing options, never as
  overdue. This flag drives both queue ordering and the report's lead section.

### 4.4 REPORT — `FR-SCOUT-4xx`  (owned by WP-5)

- **FR-SCOUT-401** — Scout shall generate a **Grant Scout Intelligence Report** (weekly
  digest) summarizing candidates discovered since a given date (defaulting to the last
  scan), led by **"Act Now"** items (eligible strong matches with near deadlines), then
  other strong matches, then remaining candidates to review — using the format in §7.
- **FR-SCOUT-402** — The report shall be produced from DB state via a Jinja2 template
  (no AI), and be available as Markdown, downloadable in the UI, and generatable from
  the CLI scan (`--report`).
- **FR-SCOUT-403** — The report shall list, per candidate: title, funder, amount range,
  deadline (with urgency tier), eligibility, fit score, source URL, and a one-line "why
  it fits" derived deterministically from the *actually matched* criteria (naming the
  matched focus area + geography, not a generic phrase). Fields whose extraction
  confidence is below 0.5 shall be rendered as unverified (e.g. `deadline ~ Sep 17,
  2026 (unverified — confirm on funder site)`), so the report never presents a guess as
  fact.
- **FR-SCOUT-404** — Report generation shall never mutate candidate state (read-only).

### 4.5 Non-functional — `NFR-SCOUT-xxx`

- **NFR-SCOUT-001** (determinism) — Evaluate + report are pure functions of DB state +
  criteria; same inputs → same outputs.
- **NFR-SCOUT-002** (no paid AI) — No component calls any paid AI API.
- **NFR-SCOUT-003** (human-in-the-loop) — No candidate becomes a Grant without explicit
  human import. Evaluate/report never auto-import.
- **NFR-SCOUT-004** (politeness) — A full sweep respects per-host rate limits, caching,
  and robots.txt, and completes within minutes for a weekly scheduled run.
- **NFR-SCOUT-005** (test coverage) — Every new module ships with unit tests; the
  discovery pipeline has an end-to-end integration test with all network calls mocked.
  No test reads or writes the real `data/grantnova.db` — tests use in-memory or tmp DBs.
- **NFR-SCOUT-006** (single schema source of truth) — Alembic is authoritative for the
  real database's schema. `init_db()`/`create_all` remains only for building fresh test
  DBs. A drift-guard test asserts that a schema built from `alembic upgrade head`
  contains the same tables/columns as the ORM models (catches future divergence).
- **NFR-SCOUT-007** (reversible migrations) — Every migration has a working
  `downgrade()`; a round-trip `downgrade base → upgrade head` on a throwaway DB is
  covered by a test.

---

## 5. Work packages

### WP-1 — Rename GMAS → GrantNova (code, docs, and database)  *(foundation; sequential, do first)*

**Why first:** a global rename touches 40 files + the live DB; running it before the
parallel feature WPs prevents cross-WP merge conflicts. Agent: `general-purpose`
(isolated worktree). This WP has two parts: **1A code/docs rename**, **1B database
rename + Alembic migration workout**.

#### Part 1A — Code / docs rename

**Owns:** every occurrence of `GMAS` / "Grants Manager Assistant System" in code,
config, batch script, templates, and the four core SDLC doc **titles/bodies** (99
occurrences / 40 files at plan time).

**Tasks:**
1. Replace product name in code/config: `src/utils/config.py` (`app_name` → `GrantNova`,
   User-Agent → `GrantNova-ScoutBot/1.x`, `database_url` default →
   `sqlite:///data/grantnova.db`, `log_file` → `logs/grantnova.log`), `src/app/main.py`,
   all `src/app/pages/*` page titles, `src/services/*`, `src/utils/*`,
   `src/templates/reports/weekly_report.md.j2`.
2. Rename `start_gmas.bat` → `start_grantnova.bat`; update its contents; update
   `pyproject.toml`, `.env.example` (incl. the `DATABASE_URL` example), `alembic.ini`,
   `requirements.txt`, `environment.yml` headers.
3. Update SDLC doc bodies/titles (PRD, HLD, DD, IP, Overview, Disambiguation) to
   "GrantNova". Keep versioned **filenames** unchanged in 1A (file renames + version
   bumps happen in WP-6) to avoid dangling links.
4. Leave historical AI-session transcripts untouched (they are a record).

#### Part 1B — Database rename + Alembic migration workout

**Context:** the live `data/gmas.db` is **not** under Alembic control and is missing
`discovered_candidates` (see §3.1). We rebuild a canonical DB from the migration chain
and copy the real data across — this both renames the file and fixes the drift.

**Owns:** `data/grantnova.db` (new), `scripts/migrate_gmas_to_grantnova.py` (new,
one-shot, idempotent), `src/db/database.py` (docstring note that Alembic is
authoritative for the real DB), and a drift/round-trip test
`tests/integration/test_migrations.py` (new).

**Tasks (ordered — safety first):**
1. **Backup** the live DB: copy `data/gmas.db` (+ `-wal`/`-shm`) →
   `data/backups/gmas.db.pre-grantnova-<YYYYMMDD>.bak`.
2. **Checkpoint WAL** so uncommitted `-wal` data is flushed
   (`PRAGMA wal_checkpoint(TRUNCATE)`) before any copy.
3. **Build canonical `data/grantnova.db` from Alembic:** with `DATABASE_URL` pointed at
   the new file, run `alembic upgrade head` against the empty file → creates the full
   001→004 schema and stamps `alembic_version`. (004 is delivered by WP-4; until then
   head is 003 and this step is re-run after WP-4 to add the evaluation columns.)
4. **Copy data** old→new via `scripts/migrate_gmas_to_grantnova.py`: transfer
   `organizations`, `funders`, `selection_criteria`, `templates` (and any non-empty
   tables), preserving primary keys; idempotent (safe to re-run).
5. **Retire** `data/gmas.db` (delete after backup confirmed); update `.gitignore` if the
   db filename is listed.

**Acceptance Criteria:**
- **AC-SCOUT-REN-01** — No active source/config/template file contains "GMAS".
  VERIFY: `grep -rn "GMAS" src scripts *.toml *.ini *.yml *.bat 2>/dev/null | wc -l` → `0`.
- **AC-SCOUT-REN-02** — Suite still green after rename.
  VERIFY: `python -m pytest -q` → `>=127 passed`.
- **AC-SCOUT-REN-03** — App boots under the new name against the new DB.
  VERIFY: `python -c "from src.utils.config import get_settings as g; print(g().app_name, g().database_url)"`
  → `GrantNova sqlite:///data/grantnova.db`.
- **AC-SCOUT-REN-04** — Launch script renamed.
  VERIFY: `test -f start_grantnova.bat && ! test -f start_gmas.bat && echo OK` → `OK`.
- **AC-SCOUT-DB-01** — Backup exists before any destructive step.
  VERIFY: `ls data/backups/gmas.db.pre-grantnova-*.bak` succeeds.
- **AC-SCOUT-DB-02** — New DB is Alembic-versioned at head with the discovery table.
  VERIFY: `alembic current` → head revision; and
  `python -c "import sqlite3;c=sqlite3.connect('data/grantnova.db');print('discovered_candidates' in [r[0] for r in c.execute(\"select name from sqlite_master where type='table'\")], 'alembic_version' in [r[0] for r in c.execute(\"select name from sqlite_master where type='table'\")])"`
  → `True True`.
- **AC-SCOUT-DB-03** — Real data preserved (no loss).
  VERIFY: row counts in `grantnova.db` match the backup for `funders` (32),
  `templates` (14), `organizations` (1), `selection_criteria` (1).
- **AC-SCOUT-DB-04** — Migrations are reversible (round-trip) and drift-free.
  VERIFY: `python -m pytest tests/integration/test_migrations.py -q` → all pass
  (covers `downgrade base → upgrade head` on a tmp DB, and the ORM-vs-migration
  drift-guard from NFR-SCOUT-006).
- **AC-SCOUT-DB-05** — Old DB retired, only the backup remains.
  VERIFY: `! test -f data/gmas.db && ls data/backups/gmas.db.pre-grantnova-*.bak` → succeeds.

---

### WP-2 — Test-harden the existing discovery code  *(parallel; independent)*

**Why:** closes the biggest correctness risk (untested orchestrator + fetcher +
sources) before we build on top of them. No production code changes except bug fixes
surfaced by tests (each logged as a `D-0xx` disambiguation). Agent: `general-purpose`.
Depends on: WP-1 merged.

**Owns (new test files only):**
`tests/unit/test_discovery_service.py`, `tests/unit/test_fetcher.py`,
`tests/unit/test_grants_gov_source.py`, `tests/unit/test_web_search_source.py`,
`tests/unit/test_funder_site_source.py`.

**Tasks:** write unit tests with **all network mocked** (monkeypatch `httpx`,
`RobotFileParser`, and injected `search_fn`). Use the existing in-memory DB fixture
pattern from `tests/conftest.py` for the service tests.

**Acceptance Criteria:**
- **AC-SCOUT-TST-01** — Fetcher honors robots + rate-limit + cache.
  VERIFY: `python -m pytest tests/unit/test_fetcher.py -q` → all pass; includes a test
  where a disallowed URL returns `None` and a cached URL skips the network.
- **AC-SCOUT-TST-02** — grants.gov connector maps API JSON → candidates and is disabled-safe.
  VERIFY: `python -m pytest tests/unit/test_grants_gov_source.py -q` → all pass.
- **AC-SCOUT-TST-03** — web_search + funder_site connectors extract via mocked fetch and
  drop ToS-blocked domains.
  VERIFY: `python -m pytest tests/unit/test_web_search_source.py tests/unit/test_funder_site_source.py -q` → all pass.
- **AC-SCOUT-TST-04** — DiscoveryService stages, dedup-flags, and imports correctly.
  VERIFY: `python -m pytest tests/unit/test_discovery_service.py -q` → all pass;
  includes: staging skips duplicate URLs; a title/URL match sets status `DUPLICATE`;
  `import_candidate` creates a Grant and sets status `IMPORTED`.
- **AC-SCOUT-TST-05** — Full suite grows and stays green.
  VERIFY: `python -m pytest -q` → `>=127 passed` (target ≥150).

---

### WP-3 — (folded into WP-2)  *HUNT/GATHER are already built; only tests were missing.*

*No separate build work; requirements FR-SCOUT-1xx/2xx are satisfied by existing code
and verified by WP-2.*

---

### WP-4 — EVALUATE: pre-review scoring, eligibility, ranked green queue

**Agent:** `general-purpose`. **Depends on:** WP-1, and WP-2's `test_discovery_service`
(so we modify the service against a green safety net).

**Owns:**
- NEW `src/discovery/evaluator.py` — `evaluate_candidate(extracted, org_profile,
  criteria) -> CandidateEvaluation{fit_score, eligibility_status, is_strong_match,
  reasons: list[str]}`. Reuses `src/engine/scoring_engine.py`; no new scoring logic.
- EDIT `src/models/discovered_candidate.py` — add `fit_score: float|None`,
  `eligibility_status: Enum(ELIGIBLE|INELIGIBLE|UNKNOWN)`, `is_strong_match: bool`,
  `why_fits: str|None`.
- NEW `src/db/migrations/versions/004_candidate_evaluation.py`.
- EDIT `src/services/discovery_service.py` — call evaluator inside `_stage_candidates`;
  add `reevaluate_candidates(db)`; make `list_candidates` rank by
  `(is_strong_match desc, eligibility ELIGIBLE first, fit_score desc, discovered_at desc)`.
- NEW `tests/unit/test_candidate_evaluator.py`,
  `tests/integration/test_scout_pipeline.py`.

**Acceptance Criteria:**
- **AC-SCOUT-EVAL-01** — Staging scores candidates (FR-SCOUT-301).
  VERIFY: `python -m pytest tests/unit/test_discovery_service.py -k evaluate -q` → pass;
  a staged candidate has a non-null `fit_score` in `[0,10]`.
- **AC-SCOUT-EVAL-02** — Hard filter sets eligibility (FR-SCOUT-302).
  VERIFY: `python -m pytest tests/unit/test_candidate_evaluator.py -k eligibility -q` →
  pass; a 501(c)(3)-required candidate against a non-501(c)(3) org →
  `eligibility_status == INELIGIBLE`.
- **AC-SCOUT-EVAL-03** — Queue is ranked, strong matches first (FR-SCOUT-303/304).
  VERIFY: `python -m pytest tests/unit/test_discovery_service.py -k ranked -q` → pass;
  `list_candidates` returns strong eligible matches (🟢, score ≥7) before others.
- **AC-SCOUT-EVAL-04** — Re-evaluation is idempotent (FR-SCOUT-305).
  VERIFY: `python -m pytest tests/unit/test_discovery_service.py -k reevaluate -q` →
  pass; row count unchanged, scores updated.
- **AC-SCOUT-EVAL-05** — Migration applies cleanly.
  VERIFY: `python -c "from alembic.config import CfgHelper" ` replaced by →
  `python -m pytest tests/integration/test_scout_pipeline.py -q` → pass (fixture builds
  schema through 004 and runs search→stage→evaluate).
- **AC-SCOUT-EVAL-06** — Nothing auto-imports (NFR-SCOUT-003).
  VERIFY: pipeline test asserts zero `Grant` rows created by evaluate; only staged
  candidates exist until an explicit `import_candidate` call.

---

### WP-5 — REPORT: Grant Scout Intelligence Report (weekly digest)

**Agent:** `general-purpose`. **Depends on:** WP-4 (ranking + `why_fits`).

**Owns:**
- NEW `src/services/scout_report_service.py` — `generate_report(db, since: date|None)
  -> ScoutReport{markdown, counts, generated_at}`; read-only.
- NEW `src/templates/reports/scout_digest.md.j2` — the §7 format.
- EDIT `scripts/run_discovery_scan.py` — add `--report` (print/save digest after scan).
- NEW `tests/unit/test_scout_report.py`.

**Acceptance Criteria:**
- **AC-SCOUT-RPT-01** — Report renders from DB state (FR-SCOUT-401/402).
  VERIFY: `python -m pytest tests/unit/test_scout_report.py -k renders -q` → pass;
  output contains the header "GRANT SCOUT INTELLIGENCE REPORT" and one block per
  candidate.
- **AC-SCOUT-RPT-02** — Strong matches listed first with required fields (FR-SCOUT-403).
  VERIFY: `python -m pytest tests/unit/test_scout_report.py -k ordering -q` → pass;
  each block shows funder, amount, deadline, eligibility, fit score, URL, why-it-fits.
- **AC-SCOUT-RPT-03** — Report is read-only (FR-SCOUT-404).
  VERIFY: `python -m pytest tests/unit/test_scout_report.py -k readonly -q` → pass;
  candidate statuses unchanged before/after generation.
- **AC-SCOUT-RPT-04** — CLI produces a digest.
  VERIFY: `python -m scripts.run_discovery_scan --report --queries "test"` exits `0`
  and prints a report to stdout (network mocked or empty-safe).

---

### WP-6 — SDLC integration + UI (Scout page) + naming finalization

**Agent:** `general-purpose`. **Depends on:** WP-4, WP-5 (so docs/UI describe real
behavior). Split into two independently verifiable halves:

**6a — UI:**
- EDIT `src/app/pages/09_discover.py` → reframe as **"🛰️ Grant Scout"**: ranked review
  queue with 🟢 strong-match highlighting + "hide ineligible" toggle; a **Report** tab
  that renders + downloads the digest; keep Search / Scrape URL / CSV tabs.
- EDIT `src/app/main.py` sidebar/nav label to "Grant Scout".

**6b — Docs:** author `FR-SCOUT`/`NFR-SCOUT` into version-bumped docs and record
decisions:
- PRD → **v1.2.0** (new §2.13 "Grant Scout"), HLD → **v1.2.0** (Scout subsystem +
  data flow), DD → **v1.2.0** (evaluator, report service, migration 004, ranked query),
  Overview → **v1.2.0** (Scout as a component + "Find" pillar), IP updated. Archive
  superseded versions to `old-versions-archive/` per existing convention.
- Reconcile `D-016`–`D-019` and add `D-020+` for every judgment call made in WP-1..5.

**Acceptance Criteria:**
- **AC-SCOUT-UI-01** — Scout page imports and renders without error (smoke).
  VERIFY: `python -c "import importlib.util,sys; s=importlib.util.spec_from_file_location('p','src/app/pages/09_discover.py'); m=importlib.util.module_from_spec(s)"`
  compiles; plus manual `streamlit run src/app/main.py` walkthrough by orchestrator
  (ranked queue shows 🟢; Report tab downloads a digest).
- **AC-SCOUT-UI-02** — Nav shows "Grant Scout".
  VERIFY: `grep -c "Grant Scout" src/app/pages/09_discover.py` → `>=1`.
- **AC-SCOUT-DOC-01** — Requirements exist and trace to code.
  VERIFY: `grep -c "FR-SCOUT-" 00_Project_Planning/01_PRD_v1.2.0.md` → `>=15`; each
  FR-SCOUT-3xx/4xx references its implementing file.
- **AC-SCOUT-DOC-02** — Version bumps + archives present.
  VERIFY: `ls 00_Project_Planning/01_PRD_v1.2.0.md 00_Project_Planning/02_High_Level_Design_v1.2.0.md` succeeds; superseded v1.1.0 copies moved to `old-versions-archive/`.
- **AC-SCOUT-DOC-03** — Disambiguation updated.
  VERIFY: `grep -c "^## D-02" 00_Project_Planning/DISAMBIGUATION_RECORD_v1.0.md` → `>=1`.

---

## 6. Orchestration sequence & phase gates

```
Phase 1 (sequential):        WP-1 Rename ──► [GATE: 127 passed, app_name=GrantNova] ──► commit
Phase 2 (parallel):          WP-2 Tests  ║  WP-6b Docs-draft (skeleton) ──► [GATE: suite green]
Phase 3 (feature):           WP-4 Evaluate ──► [GATE: eval ACs] ──► WP-5 Report ──► [GATE: report ACs]
Phase 4 (surface + finalize):WP-6a UI  ║  WP-6b Docs-finalize ──► [GATE: all ACs] ──► commit
```

- **Parallel WPs** run in separate git worktrees to avoid collisions; the orchestrator
  merges each only after its ACs pass.
- **Every gate** = the orchestrator personally runs the listed VERIFY commands. A red
  VERIFY sends the WP back to its agent with the failing output attached — never a
  patch-over.
- **Commits** happen only at phase boundaries, only after a full-suite green, and only
  with your go-ahead (per standing rule: no commits unless you ask).

## 7. Scout Intelligence Report format (for WP-5 template)

```
================= GRANT SCOUT INTELLIGENCE REPORT — {{ date }} =================
NEW OPPORTUNITIES: {{ total }}   |   STRONG MATCHES 🟢: {{ strong }}

── STRONG MATCHES (eligible, fit ≥ 7) ──────────────────────────────
{{ n }}. {{ title }}
    Funder:    {{ funder }}
    Amount:    {{ amount_min }}–{{ amount_max }}
    Deadline:  {{ deadline }}   ({{ urgency }})
    Eligible:  ✅ {{ eligibility }}
    Fit:       {{ fit_score }}/10
    Why fits:  {{ why_fits }}
    Link:      {{ source_url }}

── OTHER CANDIDATES TO REVIEW ──────────────────────────────────────
（ranked, no red flags — lower fit or eligibility unknown）

── RECURRING FUNDERS TO WATCH ──────────────────────────────────────
NOTES: {{ notes if notes }}
====================================================================
```

## 8. Deliverables checklist

- [ ] System renamed to GrantNova — code, docs (WP-1A)
- [ ] `data/gmas.db` → `data/grantnova.db`, Alembic-versioned, data preserved, reversible (WP-1B)
- [ ] Discovery pipeline test-hardened, suite ≥150 green (WP-2)
- [ ] `evaluator.py` + migration 004 + ranked green queue (WP-4)
- [ ] `scout_report_service.py` + digest template + CLI `--report` (WP-5)
- [ ] Grant Scout UI page + nav (WP-6a)
- [ ] PRD/HLD/DD/Overview v1.2.0 with FR-SCOUT/NFR-SCOUT + D-020+ (WP-6b)
- [ ] Final full-suite green, orchestrator-verified end to end

## 9. Risks & mitigations

- **R-1 Subagent hallucination** → every task gated by an orchestrator-run VERIFY
  command; no trust-based sign-off. (Primary design goal of this plan.)
- **R-2 Rename breakage** → WP-1 is sequential and gated on `127 passed` before any
  feature work builds on it.
- **R-3 DB rename data loss** → mandatory backup (AC-SCOUT-DB-01) + WAL checkpoint
  before any destructive step; canonical rebuild + verified row-count parity
  (AC-SCOUT-DB-03) rather than an in-place edit. Documented as D-020.
- **R-4 Live-network flakiness in tests** → all HTTP/robots mocked; no test hits the
  network (NFR-SCOUT-005).
- **R-5 Scope creep in EVALUATE** → evaluator *reuses* `scoring_engine`; it introduces
  no new scoring math, only applies existing scoring pre-import.
- **R-6 Schema drift (create_all vs Alembic)** → the very drift that hid the missing
  `discovered_candidates` table. Mitigated by making Alembic authoritative (NFR-SCOUT-006)
  and a drift-guard test (AC-SCOUT-DB-04). Longer term, `init_db()` should not be the
  path that provisions the production DB.
- **R-7 SQLite write contention** → the weekly scheduled scan and the Streamlit UI can
  both open the DB. WAL mode + short-lived sessions make this safe for single-user use;
  documented as a known limitation (a Postgres move is the scale path, already
  anticipated by the String-length choices in D-008).

---

## 10. Final expert review (2026-07-16)

A deliberate red-team of this plan through two lenses. Items marked **[folded in]** are
already reflected above; **[watch]** items are accepted risks to monitor during build.

### 10.1 Robust-software-development lens

1. **[folded in] Alembic was decorative, not authoritative.** The live DB was built by
   `create_all` and never migrated — it silently lacked `discovered_candidates`. Any
   plan that "just adds migration 004" on top would have failed on the real DB. WP-1B
   now rebuilds from the chain, copies data, and adds a drift-guard + round-trip test
   (NFR-SCOUT-006/007). This is the single most important correction to the plan.
2. **[folded in] Backup-before-destructive + WAL checkpoint.** A rename that deletes the
   only copy of 32 funders + 14 templates is unacceptable without a verified backup and
   a WAL flush. AC-SCOUT-DB-01/03/05 enforce it.
3. **[folded in] Tests must not touch the real DB.** Codified in NFR-SCOUT-005 so a
   stray fixture can't corrupt `grantnova.db`.
4. **[folded in] Reversibility.** Every migration must down-migrate; proven by a
   round-trip test, not by inspection.
5. **[watch] Two schema sources still coexist** after this work (`create_all` for tests,
   Alembic for prod). Acceptable now; the clean end-state is to generate test schemas
   from Alembic too. Logged as R-6.
6. **[watch] Idempotent, resumable sweeps.** A weekly sweep hitting dozens of hosts will
   partially fail; the connector-level `try/except` already isolates failures and the
   fetch cache makes re-runs cheap. Good enough; no new work.
7. **[folded in] Fail-soft evaluation.** An org with no criteria set must not crash the
   pipeline (FR-SCOUT-302 → `UNKNOWN`).

### 10.2 Grants finding & winning lens (community-level org: The Dojo — youth STEM, Somerville/Boston)

1. **[folded in] Deadlines beat fit scores in practice.** A two-person shop wins by never
   missing an *eligible, well-fit, closing-soon* opportunity. Ranking and the report now
   lead with an **"Act Now"** signal (eligible + strong + RED/YELLOW urgency), reusing
   the existing `deadline_classifier` (FR-SCOUT-306/401).
2. **[folded in] Fiscal sponsorship is an eligibility lifeline.** Many community orgs
   lack their own 501(c)(3) or apply through a sponsor. Naively hard-filtering on
   "501(c)(3) required" would wrongly discard winnable grants. FR-SCOUT-302 now treats
   *required-but-sponsorship-allowed* as ELIGIBLE.
3. **[folded in] Honesty over false confidence.** Rules-based extraction guesses; a
   grant writer who trusts a wrong deadline misses the real one. Low-confidence fields
   are now rendered as *unverified* in the report (FR-SCOUT-403), preserving trust.
4. **[folded in] "Why it fits" must be specific.** Generic blurbs waste a busy
   director's time; the line now names the matched focus area + geography.
5. **[watch] Effort-vs-award signal.** A $5k grant behind a 15-page narrative can be a
   worse use of scarce volunteer time than a $25k rolling LOI. The report surfaces
   amount + deadline so a human can judge; an explicit "burden score" is a good **v1.1
   enhancement**, deliberately deferred to avoid over-engineering v1.0.
6. **[watch] Relationships & recurring funders.** Renewals and warm funders are where
   community orgs actually win. The digest's "Recurring funders to watch" section is a
   start; deeper funder-relationship history is future scope (ties to the existing
   Funders module).
7. **[affirmed] Local-first geography.** The extractor already weights Somerville (0.85)
   / Greater Boston (0.7) above state/national — correct for a place-based youth org.
   No change needed; the plan preserves it.

### 10.3 Verdict

The plan is **sound and ready to execute** once you approve. The material change since
the first draft is WP-1B: the DB rename is no longer a cosmetic file move but a genuine,
verified Alembic migration that repairs a real latent defect — exactly the "good
workout" you asked for. Scope remains disciplined: no new scoring math, no paid AI,
human-in-the-loop intact, and every task gated by a command I will run myself.

---

*Prepared for owner confirmation. On approval, execution begins at Phase 1 / WP-1
(1A code+docs, then 1B database), gated on a full-suite green that I run and report back.*
