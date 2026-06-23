# Grants Manager Assistant System (GMAS) - Product Requirements Document

**Version**: 1.0.0
**Created**: 2026-06-19 15:29 EST
**Modified**: 2026-06-19 15:30 EST
**AI LLM Engine**: Claude Sonnet 4.6 (claude-sonnet-4-6)
**Tech Stack**: Python · Streamlit · FastAPI · SQLAlchemy · SQLite → PostgreSQL · Anthropic Claude API · Pandas · Plotly

---

## 1. Overview

### 1.1 Purpose

The Grants Manager Assistant System (GMAS) automates and intelligently supports the full lifecycle of grant fund-raising for the **Dojo at Somernova** in Somerville, Massachusetts. The system reduces the expertise barrier, eliminates manual tracking overhead, accelerates application drafting, and enforces rigorous review — replacing a fragile, human-only process with an AI-orchestrated workflow that scales with demand.

### 1.2 Scope

**In Scope:**
- Grant discovery via AI-powered web research
- Grant evaluation, scoring, and ranking against configurable criteria
- Grant opportunity repository (database)
- Application lifecycle management from discovery through outcome
- AI-assisted application narrative drafting
- Multi-stage AI review pipeline (hallucinations, compliance, ambiguity, legal/ethics)
- Human approval gate (hard enforcement before submission)
- Submission logging and outcome tracking
- Weekly report generation (Markdown + optional Google Docs)
- Relationship and funder management
- Organization profile and supporting document management
- Local-first deployment with a path to cloud

**Out of Scope (MVP):**
- Automated submission to grant portals (always manual + human-approved)
- Email/calendar integrations (future phase)
- Multi-organization support (single org MVP)
- Financial accounting or budget management system
- CRM beyond basic funder relationship notes

### 1.3 Intended Audience

- **Primary User**: Grants manager / program coordinator at the Dojo at Somernova
- **Secondary User**: Executive director / program director reviewing recommendations
- **Technical Operator**: System administrator managing deployment and API keys

---

## 2. Functional Requirements

### 2.1 Organization Profile Management

- **FR-ORG-001**: System shall store and display the organization's mission statement, values, and program descriptions.
- **FR-ORG-002**: System shall allow editing of eligibility settings (501c3 status, fiscal sponsorship acceptance, target geography).
- **FR-ORG-003**: System shall maintain a library of reusable supporting documents (IRS determination letter, budget, program descriptions, bios).
- **FR-ORG-004**: System shall use the organization profile as the primary context source for all AI agent operations.

### 2.2 Selection Criteria and Rules Editor

- **FR-SCR-001**: System shall provide a configurable editor for grant selection criteria (geography, focus area, eligibility type, funding amount range).
- **FR-SCR-002**: System shall allow setting weight values for each criterion, used to compute fit scores.
- **FR-SCR-003**: System shall support "hard filter" rules that automatically exclude grants that fail mandatory criteria.
- **FR-SCR-004**: System shall allow saving and versioning of criteria rule sets.

### 2.3 Grant Discovery

- **FR-GD-001**: System shall provide an AI-powered Grant Scout Agent that searches the web for grant opportunities matching the Dojo's mission.
- **FR-GD-002**: The Grant Scout Agent shall search across all focus areas defined in the workflow document (youth development, STEM, climate, arts, workforce development, mental health, civic engagement).
- **FR-GD-003**: System shall allow manual entry of grants discovered outside the system.
- **FR-GD-004**: System shall detect and flag duplicate grants before insertion.
- **FR-GD-005**: Each discovered grant shall capture: funder name, grant name, amount range, deadline, eligibility requirements, 501c3 required flag, fiscal sponsorship flag, application URL, source URL, discovery date.

### 2.4 Grant Evaluation and Ranking

- **FR-GER-001**: The Grant Evaluator Agent shall automatically score each newly discovered grant against the active selection criteria.
- **FR-GER-002**: Each grant shall receive a numeric fit score (0–10) and a short explanation (2–3 sentences).
- **FR-GER-003**: System shall classify each grant by deadline urgency: RED (≤30 days), YELLOW (31–60 days), GREEN (61–90 days), GRAY (>90 days or rolling).
- **FR-GER-004**: System shall display ranked grant list sortable by fit score, deadline, amount, and urgency.
- **FR-GER-005**: System shall highlight grants with fit score ≥ 7 as "Recommended."

### 2.5 Grant Repository and Tracking

- **FR-GRT-001**: System shall maintain a database of all grant opportunities discovered.
- **FR-GRT-002**: Each grant shall have a status in the lifecycle: `DISCOVERED → EVALUATED → RECOMMENDED → APPROVED_TO_APPLY → DRAFTING → IN_REVIEW → APPROVED → SUBMITTED → TRACKING → AWARDED / REJECTED / WITHDRAWN`.
- **FR-GRT-003**: System shall display a pipeline / Kanban-style view of all grants by status.
- **FR-GRT-004**: System shall alert users when a grant deadline is approaching (configurable threshold, default 14 days).

### 2.6 Weekly Report Generation

- **FR-WR-001**: System shall generate a Weekly Grant Opportunities document with all five sections defined in the workflow (Executive Summary, Ranked Table, Recommendation Memos, Application Checklists, Relationship-Building Opportunities).
- **FR-WR-002**: Weekly reports shall be stored in the database and available for download as Markdown and/or PDF.
- **FR-WR-003**: System shall optionally publish weekly reports to a specified Google Drive folder via the Google Docs API.
- **FR-WR-004**: Weekly reports shall be auto-generated but require user confirmation before publishing.

### 2.7 Application Management

- **FR-AM-001**: System shall create an Application record for each grant the user approves to pursue.
- **FR-AM-002**: Each Application shall have a document requirements checklist (required documents, narrative questions, budget requirements, reporting requirements, funder contacts).
- **FR-AM-003**: System shall maintain version history of all application drafts.
- **FR-AM-004**: System shall auto-generate a Manifest document (audit trail) capturing every action taken, agent used, decision made, and timestamp.

### 2.8 AI Application Drafting

- **FR-AD-001**: The Application Drafter Agent shall generate narrative responses to each grant question using the organization profile and grant prompt as context.
- **FR-AD-002**: Drafts shall be organized by section/question and editable inline.
- **FR-AD-003**: All AI-generated content shall be clearly marked as AI-generated until reviewed and accepted.
- **FR-AD-004**: The Drafter Agent shall operate strictly from provided organizational context — it must not fabricate programs, metrics, or outcomes not found in the org profile.

### 2.9 AI Review Pipeline

- **FR-RP-001**: Each application draft shall pass through four sequential (or parallel) review agents before it can be submitted:
  1. **Hallucination Reviewer**: Flags any content that is not traceable to org profile or grant source
  2. **Assumption Auditor**: Lists all assumptions made and whether they are documented
  3. **Ambiguity Resolver**: Documents each ambiguity encountered, resolution approach, and decision made
  4. **Compliance Checker**: Verifies all grant instructions were followed, all fields completed, and legal/ethics alignment
- **FR-RP-002**: Each review agent shall produce a structured review report stored in the database.
- **FR-RP-003**: Any review agent finding a critical issue (hallucination, non-compliance) shall block the application from advancing until resolved.
- **FR-RP-004**: All disambiguation records shall be stored in individual records per application.

### 2.10 Approval Workflow and Hard Gate

- **FR-AG-001**: System shall enforce a hard gate: an application cannot be marked `APPROVED` or `SUBMITTED` without explicit user sign-off in the UI.
- **FR-AG-002**: System shall record who signed off, when, and at what version of the draft.
- **FR-AG-003**: System shall display a summary of all review findings before prompting for sign-off.
- **FR-AG-004**: System shall produce a final pre-submission checklist that the user must acknowledge line by line.

### 2.11 Submission Tracking

- **FR-ST-001**: System shall log the submission date, method, confirmation number (if any), and submitter name.
- **FR-ST-002**: System shall track post-submission status (pending, awarded, rejected, withdrawn) with dates and notes.
- **FR-ST-003**: System shall record award amounts when grants are awarded.

### 2.12 Funder Relationship Management

- **FR-FRM-001**: System shall maintain a funder database with contact information, relationship notes, and engagement history.
- **FR-FRM-002**: System shall identify relationship-building opportunities from grant research (funders where the Dojo should build a connection ahead of future cycles).
- **FR-FRM-003**: System shall display funding history per funder (applications submitted, awards received).

### 2.13 Dashboard and Analytics

- **FR-DA-001**: System shall display a main dashboard with: active pipeline summary, upcoming deadlines, recommended grants count, and recent activity.
- **FR-DA-002**: System shall provide analytics views: grants by status, total funding requested vs. awarded, win rate by focus area, average fit score by outcome.
- **FR-DA-003**: All analytics charts shall be interactive (Plotly).

---

## 3. Technical Requirements

### 3.1 System Level

- **TR-SL-001**: System shall be fault-tolerant; all critical operations wrapped in try-except with meaningful error messages.
- **TR-SL-002**: System shall log all operations with ISO 8601 timestamps to a rotating log file.
- **TR-SL-003**: System shall be recoverable — database state must be restorable from backup without data loss.
- **TR-SL-004**: All AI agent calls shall be logged with: agent name, prompt hash, response, tokens used, cost estimate, and timestamp.
- **TR-SL-005**: System shall run fully offline (except for AI API calls and web search) with no cloud dependencies for the core data layer.

### 3.2 Database Requirements

- **TR-DB-001**: MVP shall use SQLite; production shall support PostgreSQL migration via Alembic.
- **TR-DB-002**: Database schema shall be fully version-controlled via Alembic migration files.
- **TR-DB-003**: All tables shall include `created_at`, `updated_at`, and `is_deleted` (soft delete) columns.
- **TR-DB-004**: All AI-generated content shall be stored verbatim in the database with generation metadata.

### 3.3 AI Agent Requirements

- **TR-AI-001**: All agents shall use the Anthropic Python SDK (not OpenAI or any other provider).
- **TR-AI-002**: Agent system prompts shall be stored as versioned templates, not hardcoded strings.
- **TR-AI-003**: All agent responses shall be structured (JSON with defined schema) and validated before storage.
- **TR-AI-004**: Token usage and cost shall be tracked per agent call and aggregated by session.
- **TR-AI-005**: Web search results used by the Grant Scout Agent shall be stored with source URLs for traceability.
- **TR-AI-006**: Agents shall use temperature 0.1 for factual/review tasks and temperature 0.7 for creative drafting.

### 3.4 Development Requirements

- **TR-DV-001**: System shall use Git for version control with semantic versioning.
- **TR-DV-002**: System shall NEVER overwrite earlier file versions — all changes tracked in Git.
- **TR-DV-003**: Code shall follow PEP 8 (enforced by `ruff`) and be typed (mypy strict).
- **TR-DV-004**: Requirements shall be pinned in `requirements.txt` and `pyproject.toml`.
- **TR-DV-005**: All secrets (API keys, credentials) shall be managed via `.env` file, never committed to Git.

### 3.5 Testing Requirements

- **TR-TD-001**: Unit test coverage shall be ≥ 80% for all service and model modules.
- **TR-TD-002**: Integration tests shall cover all database CRUD operations and agent call flows.
- **TR-TD-003**: All tests shall run via `pytest` with fixtures for database and mock AI responses.
- **TR-TD-004**: CI/CD pipeline shall run tests on every commit.

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
| DR-007 | Technical Documentation | Developer reference (APIs, models, agents) |
| DR-008 | Deployment Guide | Local and cloud deployment procedures |
| DR-009 | CHANGELOG | Version history |

---

## 5. Non-Functional Requirements

### 5.1 Performance

- **NFR-P-001**: UI pages shall load within 3 seconds on local deployment.
- **NFR-P-002**: Grant Scout Agent shall complete a full weekly search cycle within 10 minutes.
- **NFR-P-003**: Application Drafter Agent shall produce a complete draft (up to 10 sections) within 5 minutes.
- **NFR-P-004**: Database queries shall execute within 500ms for standard operations.

### 5.2 Usability

- **NFR-U-001**: The interface shall be operable by a non-technical grants manager without developer assistance.
- **NFR-U-002**: All AI-generated content shall be visually distinguished from user-entered content.
- **NFR-U-003**: Every potentially destructive action (delete, submit, override) shall require confirmation.
- **NFR-U-004**: The weekly grant cycle (search → review → report) shall be completable in 3 or fewer clicks from the dashboard.

### 5.3 Security

- **NFR-S-001**: API keys shall never be rendered in the UI or logged in plain text.
- **NFR-S-002**: SQL injection shall be prevented through exclusive use of SQLAlchemy ORM (no raw SQL).
- **NFR-S-003**: All user inputs shall be validated and sanitized before processing or storage.
- **NFR-S-004**: The approval gate shall be enforced in code (not just UI) — no database record shall be set to SUBMITTED status without a corresponding approval record.

### 5.4 Reliability

- **NFR-R-001**: System shall handle AI API failures gracefully with retry logic (3 attempts, exponential backoff).
- **NFR-R-002**: Failed agent runs shall be logged and resumable — partial results are never silently discarded.
- **NFR-R-003**: SQLite database shall be backed up automatically before any destructive migration.

---

## 6. Future Enhancements

### 6.1 Post-MVP Features

- **FE-001**: Multi-user support with role-based access (Researcher, Drafter, Approver, Admin)
- **FE-002**: Email notification integration (deadline alerts, approval requests)
- **FE-003**: Calendar integration for deadline management (Google Calendar / Outlook)
- **FE-004**: Automated portal form-filling (browser automation for known grant portals)
- **FE-005**: Grants database integration (Candid/Foundation Directory, Instrumentl API)
- **FE-006**: Budget template builder integrated with application workflow
- **FE-007**: Post-award grant management (reporting requirements, milestone tracking)

### 6.2 Integration Opportunities

- **FE-INT-001**: Google Workspace (Docs, Drive, Sheets) — full bidirectional sync
- **FE-INT-002**: Instrumentl or Candid APIs for expanded grant databases
- **FE-INT-003**: Salesforce Nonprofit or HubSpot for CRM integration
- **FE-INT-004**: Slack notifications for deadline alerts and approval requests

### 6.3 Scalability

- **FE-SCALE-001**: Multi-organization support (GMAS as a SaaS platform)
- **FE-SCALE-002**: Agent result caching layer (Redis) for repeated grant research
- **FE-SCALE-003**: PostgreSQL migration for high-concurrency production deployment
- **FE-SCALE-004**: Async agent execution via FastAPI background tasks

---

## 7. Constraints and Assumptions

### 7.1 Constraints

- System must run locally on a standard Windows 11 laptop for the MVP.
- All AI capabilities require an active Anthropic API key (billable usage).
- Google Docs integration requires a Google Cloud project and OAuth credentials (optional feature).
- Web search capabilities depend on Claude's built-in search tool or a third-party search API (Tavily).
- No grant application may be submitted by the system — submission is always a manual human action.

### 7.2 Assumptions

- The Dojo at Somernova has or can obtain an Anthropic API key.
- The primary user has sufficient familiarity with grant processes to review AI recommendations intelligently.
- The organization profile (mission, programs, documents) will be kept up-to-date by the user.
- Selection criteria will be reviewed and updated at least quarterly.
- Initial deployment is single-user; multi-user support is a post-MVP enhancement.

---

## 8. Change Log

### Version 1.0.0 (2026-06-19)
- Initial PRD created from kickoff prompt and workflow document analysis.
- Adapted from PRD Template v4.0.0.

---

**Document Version**: 1.0.0 | 2026-06-19
**Template Based On**: 01_Product_Reqts_Doc_Template_GENERIC_v4.0.0.md
