# Grants Manager Assistant System (GMAS) - High-Level Design Document

**Version**: 1.0.0
**Created**: 2026-06-19 15:29 EST
**Modified**: 2026-06-19 15:30 EST
**AI LLM Engine**: Claude Sonnet 4.6 (claude-sonnet-4-6)
**Tech Stack**: Python · Streamlit · SQLAlchemy · SQLite → PostgreSQL · Anthropic Claude API · Pandas · Plotly

---

## 1. Introduction

### 1.1 Purpose

This document translates the GMAS Product Requirements Document (PRD v1.0.0) into a technical architecture, describing how the system's components are structured, how they interact, and the key design decisions that guide implementation.

### 1.2 Scope

Covers:
- Overall system architecture and layering
- AI multi-agent orchestration design
- Database schema (entity-relationship level)
- Application state machine
- User interface structure and navigation
- Data flow through the system
- Security design
- Performance and error handling strategy
- Third-party integration design

### 1.3 Definitions

| Term | Definition |
|------|-----------|
| GMAS | Grants Manager Assistant System |
| Agent | A Claude API-powered module with a specific role and tool set |
| Orchestrator | The coordinator that dispatches and sequences agents |
| Manifest | The audit trail document auto-generated for every application |
| Fit Score | A 0–10 numeric rating of a grant's alignment with org criteria |
| Hard Gate | A code-enforced constraint that blocks submission without approval record |
| PRD | Product Requirements Document (01_PRD_v1.0.0.md) |

### 1.4 References

1. `Grants-Manager-Assistant-KICKOFF-PROMPT-v1.0.0.md`
2. `Grant-Research-Application-Assistant-Workflow-v1.0.0.md`
3. `00_Project_Plan_OVERVIEW_v1.0.0.md`
4. `01_PRD_v1.0.0.md`

---

## 2. System Architecture

### 2.1 Overall Architecture

GMAS uses a **layered, modular architecture** with five distinct layers. The AI Agent layer is the unique addition on top of a conventional Python web app stack.

```
┌────────────────────────────────────────────────────────────────┐
│                     PRESENTATION LAYER                         │
│              Streamlit Multi-Page Application                  │
│   Dashboard · Grant DB · Application Mgr · Reports · Settings  │
└─────────────────────────────┬──────────────────────────────────┘
                              │
┌─────────────────────────────▼──────────────────────────────────┐
│                      AI AGENT LAYER                            │
│   Orchestrator · Scout · Evaluator · Drafter · Reviewers       │
│              Anthropic Claude API (claude-sonnet-4-6)          │
└──────────────┬──────────────────────────────────┬──────────────┘
               │                                  │
┌──────────────▼──────────────┐   ┌───────────────▼──────────────┐
│     APPLICATION LAYER       │   │      EXTERNAL SERVICES        │
│  Business Logic & Services  │   │  Web Search · Google Docs API │
│  Scoring · Deadline · State │   │  (optional integrations)      │
│  Reports · Export           │   └───────────────────────────────┘
└──────────────┬──────────────┘
               │
┌──────────────▼──────────────────────────────────────────────────┐
│                     DATA ACCESS LAYER                           │
│              SQLAlchemy 2.x ORM + Alembic Migrations           │
└──────────────┬──────────────────────────────────────────────────┘
               │
┌──────────────▼──────────────────────────────────────────────────┐
│                      DATABASE LAYER                             │
│         SQLite (MVP, local) → PostgreSQL (production)           │
└─────────────────────────────────────────────────────────────────┘
```

### 2.2 Layer Descriptions

| Layer | Responsibility | Key Technologies |
|-------|---------------|-----------------|
| Presentation | User interactions, display, forms | Streamlit, Plotly |
| AI Agent | Intelligent research, scoring, drafting, review | Anthropic SDK, Claude API |
| Application | Business rules, scoring, state transitions, reporting | Python, Pandas |
| Data Access | ORM abstraction, query building, migrations | SQLAlchemy 2.x, Alembic |
| Database | Persistent storage | SQLite / PostgreSQL |

---

## 3. AI Multi-Agent Architecture

### 3.1 Agent Design Principles

- Each agent has a **single responsibility** and a **versioned system prompt**
- Agents receive structured input (JSON) and return structured output (JSON)
- All agent calls are logged with: agent name, model, tokens, cost, response hash
- Agents never call each other directly — all coordination runs through the Orchestrator
- Agents are stateless — all context is injected per call from the database

### 3.2 Agent Registry

| Agent ID | Name | Primary Model | Role |
|----------|------|--------------|------|
| `grant_scout` | Grant Scout Agent | claude-sonnet-4-6 | Discovers grant opportunities via web search |
| `grant_evaluator` | Grant Evaluator Agent | claude-sonnet-4-6 | Scores grants against selection criteria |
| `app_drafter` | Application Drafter Agent | claude-sonnet-4-6 | Drafts narrative responses to grant questions |
| `hallucination_reviewer` | Hallucination Reviewer | claude-opus-4-8 | Detects any content not traceable to source |
| `assumption_auditor` | Assumption Auditor | claude-opus-4-8 | Catalogs all assumptions made in draft |
| `ambiguity_resolver` | Ambiguity Resolver | claude-opus-4-8 | Documents ambiguities and resolution decisions |
| `compliance_checker` | Compliance Checker | claude-opus-4-8 | Verifies all instructions followed, fields valid, ethics aligned |
| `orchestrator` | Orchestrator | claude-sonnet-4-6 | Dispatches agents, manages workflow sequencing |

### 3.3 Orchestrator Workflow

```
WEEKLY DISCOVERY CYCLE
══════════════════════
User triggers "Run Weekly Search"
  │
  ▼
Orchestrator dispatches: grant_scout (web search per focus area)
  │
  ├── Parallel: deduplication check against existing DB
  │
  ▼
New grants stored → Orchestrator dispatches: grant_evaluator (per grant)
  │
  ▼
Fit scores + urgency flags stored → Weekly Report generated
  │
  ▼
User reviews → (optional) Approve grants to pursue


APPLICATION DRAFTING CYCLE
══════════════════════════
User selects approved grant → triggers "Start Application"
  │
  ▼
Orchestrator dispatches: app_drafter (per grant question)
  │
  ▼
Draft stored, version 1.0 created
  │
  ▼
User reviews draft → triggers "Send to Review"
  │
  ▼
Orchestrator dispatches (parallel):
  ├── hallucination_reviewer
  ├── assumption_auditor
  ├── ambiguity_resolver
  └── compliance_checker
  │
  ▼
Review reports aggregated → Manifest updated
  │
  ▼
All PASS? → User sees pre-submission checklist
  │               │
  │            Any FAIL? → User must resolve → redraft → re-review
  ▼
User explicitly signs off (HARD GATE)
  │
  ▼
Application status: APPROVED (ready for manual submission)
```

### 3.4 Agent Input/Output Schema

Every agent receives and returns a consistent structure:

**Input (AgentRequest)**
```json
{
  "agent_id": "grant_evaluator",
  "session_id": "uuid",
  "org_context": { "mission": "...", "programs": [...], "values": [...] },
  "criteria": { "rules": [...], "weights": {...} },
  "target": { "grant_id": "uuid", "grant_data": {...} },
  "prompt_version": "1.0.0"
}
```

**Output (AgentResponse)**
```json
{
  "agent_id": "grant_evaluator",
  "session_id": "uuid",
  "status": "success | error | partial",
  "result": { ... },
  "tokens_used": 1200,
  "model": "claude-sonnet-4-6",
  "generated_at": "2026-06-19T10:00:00Z",
  "prompt_hash": "sha256:..."
}
```

---

## 4. Database Design

### 4.1 Entity-Relationship Overview

```
Organization (1) ──────── has ────── (many) Documents
     │
     └── informs context for all Agents

Grant (many) ──────── belongs to ────── Funder (1)
   │
   └── (1) Application ──────── has (many) ────── DraftVersion
              │
              ├── has (many) ────── ReviewReport
              │       │
              │       └── has (many) ────── AmbiguityRecord
              │
              └── has (1) ────── Manifest

AgentLog (many) ──────── records every ────── Agent call
```

### 4.2 Core Tables

#### `organizations`
| Column | Type | Notes |
|--------|------|-------|
| id | UUID PK | |
| name | VARCHAR(255) | |
| mission | TEXT | |
| values_text | TEXT | |
| programs_json | JSON | List of program objects |
| eligibility_json | JSON | 501c3 status, fiscal sponsor, geography |
| created_at | TIMESTAMP | |
| updated_at | TIMESTAMP | |

#### `funders`
| Column | Type | Notes |
|--------|------|-------|
| id | UUID PK | |
| name | VARCHAR(255) | |
| website | VARCHAR(500) | |
| type | ENUM | foundation, government, corporate, individual |
| contact_json | JSON | Contact info |
| relationship_notes | TEXT | |
| total_awarded | DECIMAL | |
| created_at | TIMESTAMP | |
| updated_at | TIMESTAMP | |

#### `grants`
| Column | Type | Notes |
|--------|------|-------|
| id | UUID PK | |
| funder_id | UUID FK | → funders |
| name | VARCHAR(500) | |
| description | TEXT | |
| amount_min | DECIMAL | |
| amount_max | DECIMAL | |
| deadline | DATE | |
| deadline_urgency | ENUM | RED, YELLOW, GREEN, GRAY |
| eligibility_501c3_required | BOOLEAN | |
| fiscal_sponsorship_allowed | BOOLEAN | |
| geography | VARCHAR(255) | |
| focus_areas_json | JSON | List of focus areas |
| fit_score | DECIMAL(4,2) | 0.00–10.00 |
| fit_explanation | TEXT | AI-generated 2-3 sentences |
| application_url | VARCHAR(1000) | |
| source_url | VARCHAR(1000) | |
| status | ENUM | Lifecycle status |
| is_deleted | BOOLEAN | Soft delete |
| created_at | TIMESTAMP | |
| updated_at | TIMESTAMP | |

#### `selection_criteria`
| Column | Type | Notes |
|--------|------|-------|
| id | UUID PK | |
| name | VARCHAR(255) | |
| rules_json | JSON | Configurable rules and weights |
| is_active | BOOLEAN | |
| version | VARCHAR(20) | |
| created_at | TIMESTAMP | |

#### `applications`
| Column | Type | Notes |
|--------|------|-------|
| id | UUID PK | |
| grant_id | UUID FK | → grants |
| status | ENUM | Application lifecycle status |
| approved_by | VARCHAR(255) | Name of approver |
| approved_at | TIMESTAMP | |
| submitted_at | TIMESTAMP | |
| submission_confirmation | VARCHAR(500) | |
| outcome | ENUM | pending, awarded, rejected, withdrawn |
| award_amount | DECIMAL | |
| is_deleted | BOOLEAN | |
| created_at | TIMESTAMP | |
| updated_at | TIMESTAMP | |

#### `draft_versions`
| Column | Type | Notes |
|--------|------|-------|
| id | UUID PK | |
| application_id | UUID FK | → applications |
| version_number | VARCHAR(20) | e.g. "1.0", "1.1", "2.0" |
| sections_json | JSON | Array of {question, response, is_ai_generated} |
| word_count | INTEGER | |
| created_by | ENUM | user, ai_agent |
| created_at | TIMESTAMP | |

#### `review_reports`
| Column | Type | Notes |
|--------|------|-------|
| id | UUID PK | |
| application_id | UUID FK | → applications |
| draft_version_id | UUID FK | → draft_versions |
| agent_id | VARCHAR(100) | Which review agent |
| status | ENUM | PASS, FAIL, WARNING |
| findings_json | JSON | Structured list of findings |
| blocking_issues_count | INTEGER | |
| created_at | TIMESTAMP | |

#### `ambiguity_records`
| Column | Type | Notes |
|--------|------|-------|
| id | UUID PK | |
| application_id | UUID FK | → applications |
| review_report_id | UUID FK | → review_reports |
| description | TEXT | What ambiguity was encountered |
| resolution_approach | TEXT | How it was resolved |
| decision_made | TEXT | What was decided |
| created_at | TIMESTAMP | |

#### `manifests`
| Column | Type | Notes |
|--------|------|-------|
| id | UUID PK | |
| application_id | UUID FK | → applications (1:1) |
| content_json | JSON | Full audit trail of all events |
| generated_at | TIMESTAMP | |
| last_updated | TIMESTAMP | |

#### `agent_logs`
| Column | Type | Notes |
|--------|------|-------|
| id | UUID PK | |
| agent_id | VARCHAR(100) | |
| session_id | UUID | |
| model | VARCHAR(100) | |
| prompt_version | VARCHAR(20) | |
| prompt_hash | VARCHAR(100) | SHA-256 of system prompt |
| input_json | JSON | Request payload |
| output_json | JSON | Response payload |
| tokens_input | INTEGER | |
| tokens_output | INTEGER | |
| cost_usd | DECIMAL(8,4) | |
| status | ENUM | success, error, timeout |
| created_at | TIMESTAMP | |

#### `weekly_reports`
| Column | Type | Notes |
|--------|------|-------|
| id | UUID PK | |
| report_date | DATE | |
| content_markdown | TEXT | |
| grants_found_count | INTEGER | |
| urgent_count | INTEGER | |
| recommended_count | INTEGER | |
| published_to_gdocs | BOOLEAN | |
| gdocs_url | VARCHAR(1000) | |
| created_at | TIMESTAMP | |

---

## 5. User Interface Design

### 5.1 Framework: Streamlit

Streamlit is selected for the MVP because:
- Pure Python — no JavaScript required, maintainable by Python developers
- Built-in state management, data display, and charting
- Rapid iteration: new pages and features in hours, not days
- Multi-page support via `st.Page` / `pages/` directory structure
- Sufficient for a single-user or small-team internal tool

### 5.2 Navigation Structure

```
GMAS — Grants Manager Assistant System
├── 🏠 Dashboard              (main.py)
├── 🔍 Grant Discovery        (pages/01_discovery.py)
├── 📊 Grant Database         (pages/02_grants.py)
├── 📋 Applications           (pages/03_applications.py)
│   ├── Application Detail
│   ├── Draft Editor
│   └── Review Status
├── 📝 Weekly Report          (pages/04_reports.py)
├── 🤝 Funders                (pages/05_funders.py)
├── 📈 Analytics              (pages/06_analytics.py)
└── ⚙️  Settings              (pages/07_settings.py)
    ├── Organization Profile
    ├── Selection Criteria Editor
    └── API Configuration
```

### 5.3 Key Screens

**Dashboard**
- Active pipeline summary (count by status)
- Urgent deadlines widget (RED/YELLOW grants)
- Recommended grants count
- Recent agent activity log
- Quick actions: "Run Weekly Search" · "View Recommendations"

**Grant Discovery Page**
- "Run Grant Scout Agent" trigger button with progress display
- Manual grant entry form
- Search session history table

**Grant Database Page**
- Filterable/sortable table: Fit Score · Deadline · Urgency Flag · Status · Funder
- Color-coded urgency badges
- Click-through to grant detail

**Application Detail Page**
- Grant metadata at top
- Document requirements checklist
- Draft version selector + inline editor
- Review status panel (4 review agents, each with PASS/FAIL badge)
- Manifest / Audit Trail expandable section
- Approval button (disabled until all reviews PASS)

**Weekly Report Page**
- Last report display
- "Generate New Report" trigger
- Download (Markdown / PDF) + Publish to Google Docs

### 5.4 Design System

- Color palette follows urgency semantics: RED `#dc3545`, YELLOW `#ffc107`, GREEN `#28a745`, GRAY `#6c757d`
- AI-generated content displayed with a blue-tinted background and `🤖 AI Generated` badge
- All approval actions use a confirmation modal
- Consistent card layout for grant summaries

---

## 6. Data Flow

### 6.1 Grant Discovery Flow

```
User → "Run Weekly Search"
  → Orchestrator → Grant Scout Agent
    → Web Search API (per focus area query)
    → Structured grant data returned
  → Deduplication Service (check against DB)
  → New grants → Grant table (status: DISCOVERED)
  → Grant Evaluator Agent (per new grant)
    → Scoring Service → fit_score, fit_explanation stored
    → Deadline Service → urgency flag stored
  → Weekly Report Service → report generated
  → User notified: "X new grants found, Y recommended"
```

### 6.2 Application Drafting Flow

```
User → selects grant → "Approve to Apply"
  → Application record created (status: APPROVED_TO_APPLY)
  → Document checklist generated from grant metadata
  → User triggers "Generate Draft"
    → Orchestrator → App Drafter Agent
      → Receives: org context + grant questions + doc library context
      → Produces: section-by-section responses
    → DraftVersion v1.0 stored
  → User reviews and edits draft inline
  → User triggers "Send to Review"
    → Orchestrator → 4 Review Agents (parallel)
    → Review reports stored
    → Manifest updated
  → If all PASS: approval button enabled
  → User signs off → status: APPROVED
  → Application ready for manual submission
```

---

## 7. Security Design

### 7.1 API Key Management

- Anthropic API key stored in `.env` file, never committed to Git
- `.env.example` provided as template with placeholder values
- Keys loaded via `python-dotenv`, accessed as `os.environ` variables only
- Keys never rendered in UI — masked display only in settings page

### 7.2 Data Protection

- All user inputs validated and length-limited before storage
- SQLAlchemy ORM used exclusively — no raw SQL string concatenation
- Soft deletes only — no permanent deletion of grant or application data
- File uploads (org documents) scanned for type; stored in `data/org_documents/`

### 7.3 Approval Gate (Code-Level Enforcement)

The `ApplicationService.submit()` method performs two hard checks before allowing status to advance:
1. Verifies a `Review` record exists for each of the 4 review agents with status `PASS`
2. Verifies an `approval_record` exists with `approved_by` and `approved_at` populated

If either check fails, a `SubmissionBlockedError` is raised regardless of UI state.

---

## 8. Performance Considerations

- Agent calls are async (via `asyncio`) when multiple agents run in parallel
- Fit score calculation is cached per (grant_id, criteria_version) pair
- Grant table uses pagination (50 rows default)
- Agent logs are archived after 90 days to a separate archive table
- Streamlit `@st.cache_data` used for heavy analytical queries

---

## 9. Error Handling and Logging

- All service methods wrapped in try/except with typed exceptions
- Logging via Python `logging` module, configured to write to `logs/gmas_YYYY-MM-DD.log`
- Log levels: DEBUG (agent internals), INFO (user actions), WARNING (recoverable issues), ERROR (failures)
- Streamlit `st.error()` displays user-friendly messages; full stack trace goes to log only
- Agent failures trigger an automatic retry (3 attempts, exponential backoff starting 2s)
- Failed agent runs stored in `agent_logs` with `status: error` — never silently dropped

---

## 10. Third-Party Integrations

| Service | Purpose | Required | Config |
|---------|---------|----------|--------|
| Anthropic API | All AI agent calls | YES | `ANTHROPIC_API_KEY` in `.env` |
| Web Search (Tavily) | Grant discovery research | YES (for Scout) | `TAVILY_API_KEY` in `.env` |
| Google Docs API | Weekly report publishing | Optional | OAuth2 credentials JSON |

---

## 11. Implementation Plan Reference

Full phased implementation plan is in `04_Implementation_Plan_v1.0.0.md` (to be created after design review).

---

## 12. Appendices

### 12.1 Technology Version Targets

| Component | Technology | Target Version |
|-----------|-----------|---------------|
| Language | Python | 3.11+ |
| Web Framework | Streamlit | 1.35+ |
| ORM | SQLAlchemy | 2.0+ |
| Migrations | Alembic | 1.13+ |
| AI SDK | anthropic | 0.30+ |
| Data Processing | Pandas | 2.2+ |
| Visualization | Plotly | 5.20+ |
| HTTP Client | httpx | 0.27+ |
| Testing | pytest | 8.x |
| Linting | ruff | 0.4+ |
| Type Checking | mypy | 1.10+ |

### 12.2 Application Lifecycle States

```
DISCOVERED
  └→ EVALUATED          (after fit scoring)
       └→ RECOMMENDED   (fit score ≥ 7)
            └→ APPROVED_TO_APPLY  (user approves)
                 └→ DRAFTING      (application started)
                      └→ IN_REVIEW  (draft sent to agents)
                           └→ APPROVED  (all reviews pass + human sign-off)
                                └→ SUBMITTED  (manually submitted)
                                     ├→ AWARDED
                                     ├→ REJECTED
                                     └→ WITHDRAWN
```

---

**Document Version**: 1.0.0 | 2026-06-19
**Template Based On**: 02_High_Level_Design_Template_GENERIC.md
