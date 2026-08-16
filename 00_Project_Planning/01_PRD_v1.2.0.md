# GrantNova — Grant Scout & Management System - Product Requirements Document

**Version**: 1.2.0
**Created**: 2026-06-19 15:29 EST
**Modified**: 2026-07-16
**Change from v1.1.0**: Renamed the system to **GrantNova**. Added the **Grant Scout** module (§2.13) — the discovery/reconnaissance arm that hunts, gathers, evaluates, and reports on grant opportunities (FR-SCOUT / NFR-SCOUT). Implementation and full acceptance criteria are tracked in `05_Grant_Scout_Task_Implementation_Plan_v1.0.0.md`.
**Change from v1.0.0**: Production system redesigned to require NO paid AI services. AI used only during development (via Claude Code). All runtime intelligence is rules-based, template-driven, and human-guided.

**AI LLM Engine (Development Only)**: Claude Sonnet 4.6 — used to BUILD this system, not to RUN it.
**Tech Stack**: Python · Streamlit · SQLAlchemy · SQLite → PostgreSQL · Pandas · Plotly · Jinja2

---

## 1. Overview

### 1.1 Purpose

The GrantNova — Grant Scout & Management System provides the Dojo at Somernova with a structured, intelligent workflow management tool that covers the full lifecycle of grant fund-raising — from discovery through award — without requiring any paid AI services to operate. The system lowers the expertise barrier, eliminates manual tracking overhead, accelerates application drafting through reusable templates, and enforces rigorous review processes. All of this runs locally as a traditional web application with no ongoing subscription costs.

### 1.2 Scope

**In Scope:**
- Grant repository with CRUD operations and metadata tracking
- Manual grant entry and CSV/Excel import
- Rules-based scoring engine with configurable weighted criteria
- Grant opportunity ranking by fit score and deadline urgency
- Application lifecycle management (discovery through award outcome)
- Template library for application narrative drafting
- Four-category structured human review checklists
- Human approval gate (code-enforced before any submission)
- Submission logging and outcome tracking
- Auto-generated manifest (audit trail) per application
- Weekly Grant Opportunities report (generated from database)
- Funder relationship management
- Organization profile and supporting document management
- Optional local AI assistance via Ollama (free, runs locally, not required)
- Local-first deployment with a path to cloud

**Out of Scope (All Versions):**
- Any paid AI API service as a REQUIRED production dependency
- Automated submission to grant portals (always human approved and manually submitted by a human)
- Automated web crawling of grant portals (user does web research, enters grants manually or via import)

**Out of Scope (MVP — Future Phases):**
- Email/calendar integrations
- Multi-organization support
- Financial accounting / budget management
- Full CRM beyond basic funder relationship notes
- Optional Ollama AI features (Phase 7 — after core is complete)

### 1.3 Intended Audience

- **Primary User**: Grants manager / program coordinator at the Dojo at Somernova
- **Secondary User**: Executive director / program director reviewing recommendations and signing off
- **Technical Operator**: Person managing local installation and updates

---

## 2. Functional Requirements

### 2.1 Organization Profile Management

- **FR-ORG-001**: System shall store and display the organization's name, mission statement, values, and program descriptions.
- **FR-ORG-002**: System shall allow editing of eligibility settings (501c3 status, fiscal sponsorship acceptance, target geography).
- **FR-ORG-003**: System shall maintain a library of reusable supporting documents (IRS determination letter, budget, program descriptions, leadership bios).
- **FR-ORG-004**: System shall use the organization profile as the primary context source for scoring and template generation.
- **FR-ORG-005**: System shall support multiple versions of key documents (e.g., current year budget vs. prior year budget).

### 2.2 Selection Criteria and Rules Editor

- **FR-SCR-001**: System shall provide a configurable editor for grant selection criteria, including geography, focus area, eligibility type, and funding amount range.
- **FR-SCR-002**: System shall allow assigning weight values (0–10) to each criterion, used in the weighted fit score calculation.
- **FR-SCR-003**: System shall support "hard filter" rules that automatically set the fit score to 0 for grants failing a mandatory criterion (e.g., wrong geography, requires 501c3 when org does not have it).
- **FR-SCR-004**: System shall allow saving and labeling multiple criteria rule sets (e.g., "Standard," "Climate-Focused," "Workforce-Only").
- **FR-SCR-005**: System shall display which criteria version was active when a grant was scored, for audit purposes.

### 2.3 Grant Entry and Repository

- **FR-GE-001**: System shall provide a form for manually entering all grant metadata: funder name, grant name, amount range, deadline, eligibility requirements, 501c3 required flag, fiscal sponsorship flag, focus areas, application URL, source URL, and notes.
- **FR-GE-002**: System shall support bulk import of grants from a CSV or Excel file with a defined column schema.
- **FR-GE-003**: System shall detect and flag potential duplicate grants before insertion (matching on grant name + funder name, and on application URL).
- **FR-GE-004**: System shall allow editing of all grant fields after entry.
- **FR-GE-005**: System shall implement soft delete (archive) for grants — no permanent deletion of records.

### 2.4 Rules-Based Grant Scoring

- **FR-GS-001**: System shall automatically calculate a fit score (0.00–10.00) for each grant using the active criteria rule set.
- **FR-GS-002**: The fit score shall be computed as a weighted sum: for each criterion, if the grant matches, that criterion's weight contributes to the score; if not, it does not. The total is normalized to a 0–10 scale.
- **FR-GS-003**: System shall display a score explanation showing which criteria the grant matched and which it did not, with weight contributions.
- **FR-GS-004**: System shall re-score grants automatically when the active criteria rule set is updated.
- **FR-GS-005**: System shall flag grants with a fit score ≥ 7 as "Recommended."

### 2.5 Deadline Urgency Classification

- **FR-DU-001**: System shall classify each grant by deadline urgency: RED (≤ 30 days), YELLOW (31–60 days), GREEN (61–90 days), GRAY (> 90 days or rolling deadline).
- **FR-DU-002**: System shall display urgency badges prominently in all grant list views.
- **FR-DU-003**: System shall alert the user when any tracked grant's deadline falls within a configurable threshold (default: 14 days).
- **FR-DU-004**: System shall recalculate urgency classification daily on app load.

### 2.6 Grant Pipeline View

- **FR-GP-001**: System shall display all grants in a filterable, sortable table view.
- **FR-GP-002**: Filters shall include: urgency tier, status, focus area, amount range, fit score minimum, 501c3 required, fiscal sponsorship allowed.
- **FR-GP-003**: System shall display a Kanban-style pipeline view of grants grouped by lifecycle status.
- **FR-GP-004**: System shall display a summary count of grants by status on the dashboard.

### 2.7 Weekly Grant Opportunities Report

- **FR-WR-001**: System shall generate a Weekly Grant Opportunities document with all five sections: Executive Summary, Ranked Grant Table, Recommendation Memos (fit score ≥ 7), Application Checklists (fit score ≥ 7), and Relationship-Building Opportunities.
- **FR-WR-002**: The report shall be generated from the current database state using Jinja2 templates — no AI required.
- **FR-WR-003**: Reports shall be stored in the database and downloadable as Markdown and PDF.
- **FR-WR-004**: System shall optionally publish reports to a specified Google Drive folder (requires user-provided Google OAuth credentials).
- **FR-WR-005**: Report generation shall be user-triggered and display a preview before finalizing.

### 2.8 Application Management

- **FR-AM-001**: System shall create an Application record when the user approves a grant to pursue.
- **FR-AM-002**: Each Application shall have a document requirements checklist auto-populated from grant metadata (required documents, narrative questions, budget format, reporting requirements, funder contact).
- **FR-AM-003**: System shall maintain version history of all application drafts (v1.0, v1.1, v2.0, etc.).
- **FR-AM-004**: System shall auto-generate and maintain a Manifest document (audit trail) capturing every action, decision, and timestamp for the application.
- **FR-AM-005**: System shall display the application lifecycle status prominently and allow advancing status only through valid transitions.

### 2.9 Template Library for Drafting

- **FR-TL-001**: System shall maintain a library of reusable paragraph templates organized by grant question type (mission alignment, population served, program description, need statement, evaluation plan, budget narrative, sustainability plan, etc.).
- **FR-TL-002**: System shall allow users to select relevant templates, which are pre-populated into the draft editor for customization.
- **FR-TL-003**: System shall support creating, editing, and tagging custom templates from accepted application language.
- **FR-TL-004**: System shall track which templates were used in each draft version.
- **FR-TL-005**: System shall clearly indicate which draft content originated from a template (pre-fills) vs. was written by the user.

### 2.10 Structured Human Review Pipeline

The review pipeline provides four human-completed checklists per application draft. These replace AI review agents with a structured, guided human process that is equally rigorous.

- **FR-RP-001**: System shall provide four distinct review checklists for each application draft:
  - **Review 1 — Fact Verification Checklist**: User verifies each factual claim in the draft traces back to an org document or verifiable source (equivalent to hallucination detection).
  - **Review 2 — Assumption Log**: User documents every assumption made in the draft (equivalent to assumption auditing).
  - **Review 3 — Ambiguity Resolution Record**: User documents each ambiguous grant instruction, the resolution approach, and the decision made.
  - **Review 4 — Compliance Checklist**: User verifies all grant instructions are followed, all required fields are completed, and content is aligned with legal/ethics policies.
- **FR-RP-002**: Each checklist shall have line-item completion tracking — users check off each item individually.
- **FR-RP-003**: System shall flag any checklist item marked with a critical finding and prevent advancement until resolved.
- **FR-RP-004**: All disambiguation records and assumption logs shall be stored as individual records per application in the database.
- **FR-RP-005**: System shall display an aggregate review status (all four checklists) in the application overview.

### 2.11 Approval Workflow and Hard Gate

- **FR-AG-001**: System shall enforce a hard gate: an application CANNOT advance to APPROVED or SUBMITTED status without all four review checklists marked complete with no unresolved critical items.
- **FR-AG-002**: System shall additionally require explicit human sign-off: the user must complete a pre-submission acknowledgment checklist confirming each major step was completed.
- **FR-AG-003**: System shall record the approver's name, timestamp, and the draft version that was approved.
- **FR-AG-004**: The hard gate shall be enforced at the service layer in code — not only in the UI — so it cannot be bypassed by any means.

### 2.12 Submission Tracking

- **FR-ST-001**: System shall log the submission date, submission method, confirmation number (if any), and name of person who submitted.
- **FR-ST-002**: System shall track post-submission status: PENDING, AWARDED, REJECTED, WITHDRAWN.
- **FR-ST-003**: System shall record award amounts and award dates when grants are awarded.
- **FR-ST-004**: System shall calculate and display a running win rate and total funding awarded.

### 2.13 Funder Relationship Management

- **FR-FRM-001**: System shall maintain a funder database with: funder name, website, type (foundation/government/corporate/other), contact information, and relationship notes.
- **FR-FRM-002**: System shall display per-funder history: grants applied, awards received, total funding.
- **FR-FRM-003**: System shall include a "Relationship-Building Opportunities" section in the weekly report identifying funders worth cultivating.

### 2.14 Dashboard and Analytics

- **FR-DA-001**: Main dashboard shall display: active pipeline summary (count by status), upcoming deadlines (next 30 days), recommended grants count, recent activity log, and quick-action buttons.
- **FR-DA-002**: Analytics page shall provide: grants by status chart, total funding requested vs. awarded, win rate by focus area, deadline adherence rate, and average fit score by outcome.
- **FR-DA-003**: All analytics charts shall be interactive Plotly charts.
- **FR-DA-004**: Dashboard data shall refresh on each page load with no cache staleness.

### 2.15 Optional Local AI Features (Ollama)

- **FR-OAI-001**: System shall include an optional Ollama integration, disabled by default, activated via a settings toggle.
- **FR-OAI-002**: When Ollama is enabled and running locally, system shall offer: AI-assisted paragraph drafting (given a template and context), AI-assisted grant description summarization, and AI-assisted search query suggestions.
- **FR-OAI-003**: All Ollama features shall degrade gracefully to manual operation when Ollama is not running.
- **FR-OAI-004**: System shall display a clear status indicator showing whether Ollama is connected.
- **FR-OAI-005**: No Ollama feature shall be required for any core workflow — all are enhancements only.

### 2.13 Grant Scout Module (Discovery / Reconnaissance)

The Grant Scout is GrantNova's discovery arm. It **hunts** across sources, **gathers**
opportunity intelligence, **evaluates** fit + eligibility before human review, and
**reports** a weekly digest. It is no-AI (deterministic rules), ToS/robots-compliant,
and human-in-the-loop: nothing becomes a tracked Grant without explicit confirmation.
Design, data model, and full acceptance criteria live in
`05_Grant_Scout_Task_Implementation_Plan_v1.0.0.md`.

**HUNT (find):**
- **FR-SCOUT-101**: System shall discover opportunities from grants.gov (official API), web search (keyless default, pluggable provider), and known funder sites + curated public portals.
- **FR-SCOUT-102**: System shall expand the org profile into a deterministic battery of ≤40 queries (focus × geography × population × year) for a "search everywhere" sweep.
- **FR-SCOUT-103**: All discovery shall be safe with any source disabled (returns empty; never raises).

**GATHER (collect):**
- **FR-SCOUT-201**: Fetching shall honor robots.txt (default on), send a descriptive User-Agent, rate-limit per host, and cache responses to disk.
- **FR-SCOUT-202**: Field extraction shall be fully deterministic (no AI); identical input yields identical output.
- **FR-SCOUT-203**: Every extracted field shall carry a 0.0–1.0 confidence and an evidence snippet.
- **FR-SCOUT-204**: ToS-restricted aggregator domains (Instrumentl, Candid, Foundation Center) shall never be auto-fetched; Candid via official API only, Instrumentl via user-supplied CSV only.

**EVALUATE (assess fit, pre-review):**
- **FR-SCOUT-301**: When a candidate is staged, System shall compute a fit score (0.0–10.0) using the active selection-criteria rule set (reusing the scoring engine), without importing it as a Grant.
- **FR-SCOUT-302**: System shall compute an eligibility status of ELIGIBLE / INELIGIBLE / UNKNOWN via the criteria's hard filters. A grant that requires 501(c)(3) but allows a fiscal sponsor the org can use is ELIGIBLE. No active criteria → UNKNOWN with fit 0.0 (never raises).
- **FR-SCOUT-303**: The review queue shall be ranked best-first (strong matches, then ELIGIBLE, then higher fit).
- **FR-SCOUT-304**: Candidates with fit ≥ recommendation threshold AND ELIGIBLE shall be marked strong matches and surfaced with a green indicator; weak/ineligible candidates are deprioritized and hideable — never red-flagged at queue level.
- **FR-SCOUT-305**: Re-evaluation shall be idempotent and re-runnable when the active criteria change.
- **FR-SCOUT-306**: System shall classify each candidate's deadline urgency (reusing the deadline classifier) and set an "Act Now" flag when a candidate is ELIGIBLE, a strong match, and closing soon (RED/YELLOW).

**REPORT (brief the user):**
- **FR-SCOUT-401**: System shall generate a Grant Scout Intelligence Report (weekly digest) of candidates discovered since a given date, led by Act Now items then strong matches.
- **FR-SCOUT-402**: The report shall be produced from DB state via a Jinja2 template (no AI), available as Markdown in the UI and from the CLI scan (`--report`).
- **FR-SCOUT-403**: The report shall list per candidate: title, funder, amount, deadline (with urgency), eligibility, fit, source URL, and a specific "why it fits". Fields below 0.5 confidence shall be rendered as unverified.
- **FR-SCOUT-404**: Report generation shall never mutate candidate state (read-only).

**Non-functional (Scout):**
- **NFR-SCOUT-001**: Evaluate + report are pure functions of DB state + criteria (deterministic).
- **NFR-SCOUT-002**: No component calls any paid AI API.
- **NFR-SCOUT-003**: No candidate becomes a Grant without explicit human import.
- **NFR-SCOUT-004**: A full sweep respects per-host rate limits, caching, and robots.txt; completes within minutes.
- **NFR-SCOUT-005**: Every new module ships with unit tests; the pipeline has an end-to-end test with all network mocked; tests never touch the real DB.
- **NFR-SCOUT-006**: Alembic is the authoritative schema source for the real database; a drift-guard test asserts ORM/migration parity.
- **NFR-SCOUT-007**: Every migration is reversible; a round-trip test covers downgrade→upgrade.

---

## 3. Technical Requirements

### 3.1 System Level

- **TR-SL-001**: System shall NOT require any external paid AI API to start, run, or complete any core workflow.
- **TR-SL-002**: System shall be fault-tolerant — all critical operations wrapped in try/except with meaningful, user-friendly error messages.
- **TR-SL-003**: System shall log all operations with ISO 8601 timestamps to a rotating log file.
- **TR-SL-004**: System shall be recoverable — database state must be restorable from backup without data loss.
- **TR-SL-005**: System shall run fully offline (including the core grant tracking and review workflow) with no internet dependencies.
- **TR-SL-006**: Internet access is only required for: Google Docs publishing (optional), and Ollama model downloads (one-time setup, optional).

### 3.2 Database Requirements

- **TR-DB-001**: MVP shall use SQLite; production shall support PostgreSQL migration via Alembic.
- **TR-DB-002**: Database schema shall be fully version-controlled via Alembic migration files.
- **TR-DB-003**: All tables shall include `created_at`, `updated_at`, and `is_deleted` (soft delete) columns.
- **TR-DB-004**: SQLite database shall be backed up automatically before each Alembic upgrade.

### 3.3 Scoring Engine Requirements

- **TR-SE-001**: Fit score calculation shall be deterministic — same inputs always produce same outputs.
- **TR-SE-002**: Scoring logic shall be fully auditable — the score breakdown (which criteria matched, which did not, weight contributions) shall be stored with each scored grant.
- **TR-SE-003**: Hard filter evaluation shall occur before weighted scoring — a grant failing a hard filter receives score 0.00 regardless of other criteria.
- **TR-SE-004**: Score recalculation shall complete within 1 second for up to 500 grants.

### 3.4 Template System Requirements

- **TR-TS-001**: Template library shall be stored in the database (not as files) so templates are editable via the UI.
- **TR-TS-002**: Templates shall support variable placeholders (e.g., `{{program_name}}`, `{{org_name}}`) that are auto-filled from the organization profile on selection.
- **TR-TS-003**: Templates shall be versioned — updating a template shall not alter drafts that used the previous version.

### 3.5 Development Requirements

- **TR-DV-001**: System shall use Git for version control with semantic versioning.
- **TR-DV-002**: System shall NEVER overwrite earlier file versions — all changes tracked in Git.
- **TR-DV-003**: Code shall follow PEP 8 (enforced by ruff) and be typed (mypy strict).
- **TR-DV-004**: All secrets (API keys for optional features, Google OAuth) shall be in `.env` file, never committed to Git.
- **TR-DV-005**: `requirements.txt` shall not include the Anthropic SDK — it is a development-only tool, not a production dependency.

### 3.6 Testing Requirements

- **TR-TD-001**: Unit test coverage shall be ≥ 80% for all service and engine modules.
- **TR-TD-002**: Scoring engine tests shall cover: hard filter rules, weighted calculation, edge cases (all criteria match, no criteria match, partial match).
- **TR-TD-003**: Hard gate tests shall verify `SubmissionBlockedError` is raised in all non-compliant scenarios.
- **TR-TD-004**: All tests shall run with `pytest` without any API keys or external services.

---

## 4. SDLC Documentation Requirements

| ID | Document | Description |
|----|----------|-------------|
| DR-001 | PRD (this document) | Product requirements |
| DR-002 | High-Level Design | System architecture and component design |
| DR-003 | Detailed Design | Module-level implementation specifications |
| DR-004 | Implementation Plan | Development task breakdown and sequencing |
| DR-005 | Testing Plan | QA strategy, test cases, and coverage targets |
| DR-006 | User Documentation | How to operate the system (weekly cycle guide) |
| DR-007 | Technical Documentation | Developer reference |
| DR-008 | Deployment Guide | Local and cloud deployment procedures |
| DR-009 | CHANGELOG | Version history |

---

## 5. Non-Functional Requirements

### 5.1 Performance

- **NFR-P-001**: UI pages shall load within 3 seconds on local deployment.
- **NFR-P-002**: Fit score calculation for all grants shall complete within 5 seconds for up to 500 grants.
- **NFR-P-003**: Weekly report generation shall complete within 10 seconds.
- **NFR-P-004**: Database queries shall execute within 500ms for standard operations.

### 5.2 Usability

- **NFR-U-001**: The interface shall be operable by a non-technical grants manager without developer assistance.
- **NFR-U-002**: The weekly grant workflow (enter grants → score → review → report) shall be completable in under 30 minutes once data is entered.
- **NFR-U-003**: Every potentially destructive action (delete, submit, override) shall require explicit confirmation.
- **NFR-U-004**: Template-filled content shall be visually distinguished from user-entered content.

### 5.3 Security

- **NFR-S-001**: Google OAuth credentials (if used) shall never be rendered in the UI or logged.
- **NFR-S-002**: SQL injection shall be prevented through exclusive use of SQLAlchemy ORM — no raw SQL.
- **NFR-S-003**: All user inputs shall be validated and length-limited before processing or storage.
- **NFR-S-004**: The approval gate shall be enforced in the service layer — not bypassed by any UI path.

### 5.4 Reliability

- **NFR-R-001**: System shall handle all errors gracefully with user-friendly messages; full stack traces go to log only.
- **NFR-R-002**: SQLite database shall be backed up automatically before any migration.
- **NFR-R-003**: Failed operations (report generation, export) shall not corrupt the database state.
- **NFR-R-004**: If optional Ollama is unavailable, all core features shall continue to function without error.

---

## 6. Future Enhancements

### 6.1 Post-MVP Features

- **FE-001**: Multi-user support with role-based access (Researcher, Drafter, Approver, Admin)
- **FE-002**: Email notification integration for deadline alerts and approval requests
- **FE-003**: Calendar integration (Google Calendar / Outlook) for deadline management
- **FE-004**: CSV/API import from grant databases (Candid, Instrumentl) — export-format based, not requiring paid subscriptions
- **FE-005**: Budget template builder integrated with application workflow
- **FE-006**: Post-award grant management (reporting milestone tracking, outcome documentation)
- **FE-007**: Expanded template library covering all major grant question categories

### 6.2 Integration Opportunities

- **FE-INT-001**: Google Workspace (Docs, Drive, Sheets) bidirectional sync
- **FE-INT-002**: CSV export compatible with Instrumentl, Candid, and other grant tracking tools
- **FE-INT-003**: Slack notifications for deadline alerts (webhook-based, free)

### 6.3 Optional AI Enhancements (Zero-Cost Path)

- **FE-AI-001**: Expanded Ollama feature set — scoring explanation narrative, draft quality feedback
- **FE-AI-002**: User-provided API key option (Claude, OpenAI) for enhanced AI features — user's own cost, not system dependency
- **FE-AI-003**: Offline model fine-tuning on historical winning applications (advanced, post-MVP)

### 6.4 Scalability

- **FE-SCALE-001**: PostgreSQL migration for production deployment with multiple simultaneous users
- **FE-SCALE-002**: Multi-organization support (GrantNova as a shared platform for a consortium)

---

## 7. Constraints and Assumptions

### 7.1 Constraints

- System must run locally on a standard Windows 11 laptop for the MVP (no server required).
- System must function with zero paid API subscriptions or recurring software costs.
- All grant research is done manually by the user via web browser — the system manages the data, not the search.
- No grant application may be submitted by the system — submission is always a manual human action.
- Optional Ollama integration requires the user to install Ollama separately (free, one-time setup).
- Optional Google Docs integration requires the user to create a Google Cloud project (free tier sufficient).

### 7.2 Assumptions

- The primary user has sufficient grants expertise to evaluate the scored and ranked opportunities.
- The organization profile (mission, programs, documents) will be kept current by the user.
- Selection criteria will be reviewed and updated at least quarterly.
- Grant data entry is a manual step performed by the user after web research.
- Initial deployment is single-user; multi-user support is a post-MVP enhancement.

---

## 8. Change Log

### Version 1.2.0 (2026-07-16)
- Renamed the system to **GrantNova**.
- Added the **Grant Scout** module (§2.13): FR-SCOUT-1xx (Hunt), 2xx (Gather), 3xx (Evaluate), 4xx (Report) and NFR-SCOUT-001–007.
- Brought the database under Alembic control and renamed `gmas.db` → `grantnova.db`.
- See `05_Grant_Scout_Task_Implementation_Plan_v1.0.0.md` for implementation + acceptance criteria, and `DISAMBIGUATION_RECORD_v1.0.md` D-020–D-024.

### Version 1.1.0 (2026-06-19)
- **CRITICAL CHANGE**: Removed all paid AI API requirements from production system.
- Replaced AI Grant Scout Agent with manual entry + CSV import.
- Replaced AI Grant Evaluator Agent with rules-based weighted scoring engine.
- Replaced AI Application Drafter Agent with Template Library + human editing.
- Replaced AI Review Agents with four structured human review checklists.
- Added optional Ollama integration (free, local, not required).
- Added FR-SCR (Selection Criteria rules editor) — more detailed than v1.0.0.
- Added TR-SE (Scoring Engine requirements) — new section.
- Added TR-TS (Template System requirements) — new section.
- Clarified that Anthropic SDK is a DEVELOPMENT tool, not a production dependency.

### Version 1.0.0 (2026-06-19)
- Initial PRD — superseded by v1.1.0.

---

**Document Version**: 1.2.0 | 2026-07-16
**Template Based On**: 01_Product_Reqts_Doc_Template_GENERIC_v4.0.0.md
