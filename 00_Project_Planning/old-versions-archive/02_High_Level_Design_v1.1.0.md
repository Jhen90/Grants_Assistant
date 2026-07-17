# Grants Manager Assistant System (GMAS) - High-Level Design Document

**Version**: 1.1.0
**Created**: 2026-06-19 15:29 EST
**Modified**: 2026-06-19 15:30 EST
**Change from v1.0.0**: Production system redesigned with no paid AI runtime. AI agent layer removed from production architecture. Rules Engine, Template Library, and Structured Review Checklists replace AI runtime components. Optional Ollama integration added as zero-cost AI path.

**AI LLM Engine (Development Only)**: Claude Sonnet 4.6 — used to BUILD the system, not to RUN it.
**Tech Stack**: Python · Streamlit · SQLAlchemy · SQLite → PostgreSQL · Pandas · Plotly · Jinja2

---

## 1. Introduction

### 1.1 Purpose

This document translates the GMAS PRD v1.1.0 into a technical architecture describing how the system's components are structured, how they interact, and the key design decisions that guide implementation. The central architectural decision in v1.1.0 is the **removal of all paid AI runtime dependencies** from the production system.

### 1.2 Scope

Covers:
- Overall system architecture and layering (production system only)
- Distinction between development-time AI and production-time architecture
- Rules-based scoring engine design
- Template library design
- Structured human review pipeline design
- Database schema (entity-relationship level)
- Application state machine
- User interface structure and navigation
- Data flow through the system
- Optional Ollama integration
- Security, performance, and error handling strategy

### 1.3 Definitions

| Term | Definition |
|------|-----------|
| GMAS | Grants Manager Assistant System |
| Rules Engine | The deterministic, configuration-driven scoring system — replaces AI evaluator in production |
| Template Library | Database of reusable paragraph templates for grant application drafting |
| Review Checklist | One of four structured human-completed review forms per application draft |
| Manifest | The audit trail document auto-generated for every application |
| Fit Score | A 0–10 numeric rating calculated by the Rules Engine from weighted criteria |
| Hard Gate | A code-enforced constraint blocking submission without all reviews complete and approval recorded |
| Ollama | Free, locally-run open-source LLM tool — optional, not required |
| Claude Code | Development-time AI tool used to BUILD the system (not part of production) |
| PRD | Product Requirements Document (01_PRD_v1.1.0.md) |

### 1.4 References

1. `Grants-Manager-Assistant-KICKOFF-PROMPT-v1.0.0.md`
2. `Grant-Research-Application-Assistant-Workflow-v1.0.0.md`
3. `00_Project_Plan_OVERVIEW_v1.1.0.md`
4. `01_PRD_v1.1.0.md`

---

## 2. Architecture Overview: Development vs. Production

Before describing the production architecture, this section establishes the critical distinction between how AI is used during development versus how the production system operates.

### 2.1 Development Architecture (How the Software is Built)

```
┌─────────────────────────────────────────────────────────────────┐
│              DEVELOPMENT PROCESS (One-Time Build)               │
│                                                                 │
│  Claude Code Orchestrator (claude-sonnet-4-6)                   │
│      │                                                          │
│      ├── Track A Agent: Database & Infrastructure               │
│      ├── Track B Agent: Streamlit UI & Pages                    │
│      ├── Track C Agent: Business Logic & Services               │
│      ├── Track D Agent: Tests & QA                              │
│      └── Track E Agent: Documentation                           │
│                                                                 │
│  Output: Complete, tested, documented application code          │
│  Cost: One-time development session cost. No ongoing cost.      │
└─────────────────────────────────────────────────────────────────┘
                            │
                            ▼ (deploys)
             Production System (see Section 2.2)
```

### 2.2 Production Architecture (How the Software Runs — No AI Required)

```
┌─────────────────────────────────────────────────────────────────┐
│                     PRESENTATION LAYER                          │
│              Streamlit Multi-Page Application                   │
│   Dashboard · Grant DB · Applications · Reports · Settings      │
└──────────────────────────┬──────────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────────┐
│                    INTELLIGENCE LAYER                           │
│         (All logic is rules-based — no AI API calls)            │
│                                                                 │
│  ┌──────────────────┐  ┌────────────────┐  ┌────────────────┐  │
│  │  Rules Engine    │  │ Template       │  │ Review         │  │
│  │  (Scoring)       │  │ Library        │  │ Checklist      │  │
│  │                  │  │ (Drafting)     │  │ Engine         │  │
│  │ - Criteria eval  │  │ - Templates    │  │ - 4 categories │  │
│  │ - Weight calc    │  │ - Variables    │  │ - Item tracking│  │
│  │ - Hard filters   │  │ - Versioning   │  │ - Blocking     │  │
│  └──────────────────┘  └────────────────┘  └────────────────┘  │
│                                                                 │
│  ┌──────────────────┐  ┌────────────────┐                       │
│  │ Report Engine    │  │ Manifest       │                       │
│  │ (Jinja2)         │  │ Generator      │                       │
│  │ - Weekly report  │  │ - Audit trail  │                       │
│  │ - Exports        │  │ - Event log    │                       │
│  └──────────────────┘  └────────────────┘                       │
└──────────────────────────┬──────────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────────┐
│                    APPLICATION LAYER                            │
│         Business Logic Services (Python)                        │
│   GrantService · ScoringService · ApplicationService            │
│   ReviewService · ReportService · ManifestService               │
└──────────────────────────┬──────────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────────┐
│                    DATA ACCESS LAYER                            │
│              SQLAlchemy 2.x ORM + Alembic Migrations            │
└──────────────────────────┬──────────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────────┐
│                     DATABASE LAYER                              │
│          SQLite (MVP, local) → PostgreSQL (production)          │
└─────────────────────────────────────────────────────────────────┘

          ┌───────────────────────────────────────────┐
          │  OPTIONAL LOCAL AI (Zero Cost, Disabled   │
          │  by Default)                              │
          │  Ollama (llama3 / mistral / phi3)         │
          │  Connects only if user enables it in      │
          │  settings. No feature requires it.        │
          └───────────────────────────────────────────┘

          ┌───────────────────────────────────────────┐
          │  OPTIONAL EXTERNAL INTEGRATIONS           │
          │  Google Docs API (user-provided OAuth)    │
          │  No AI. No paid API required.             │
          └───────────────────────────────────────────┘
```

---

## 3. Intelligence Layer — Detailed Design

### 3.1 Rules Engine (Replaces AI Evaluator)

The Rules Engine computes a deterministic, auditable fit score for each grant.

#### 3.1.1 Scoring Algorithm

```
Fit Score = (Σ criterion_weight_i × criterion_match_i) / Σ criterion_weight_i × 10

Where:
  criterion_match_i = 1.0 if grant satisfies criterion i
                    = 0.0 if grant fails criterion i
                    = partial value (0.0–1.0) for range-based criteria

Hard Filter Check (applied first):
  If any hard_filter criterion fails → Fit Score = 0.0, process stops
```

#### 3.1.2 Criterion Types

| Type | Example | Match Logic |
|------|---------|------------|
| Geography | Target: MA/Greater Boston | 1.0 if grant.geography overlaps org.target_geographies |
| Focus Area | Target: STEM, Youth Dev | 1.0 if any grant.focus_area in org.active_focus_areas |
| Eligibility | 501c3 required? | 1.0 if org has 501c3 OR grant.fiscal_sponsorship_ok is True |
| Amount Range | Target: $5K–$100K | 1.0 if overlap; partial credit for partial overlap |
| Deadline | Within cycle window | 1.0 if not expired; partial for tight deadlines |

#### 3.1.3 Score Breakdown Storage

Every scored grant stores a `score_breakdown_json`:
```json
{
  "criteria_version": "Standard-v1",
  "hard_filter_failed": false,
  "criteria": [
    {"name": "Geography", "weight": 8, "match": 1.0, "contribution": 8.0, "reason": "Grant targets Massachusetts"},
    {"name": "Focus Area", "weight": 7, "match": 1.0, "contribution": 7.0, "reason": "STEM education matches"},
    {"name": "Eligibility", "weight": 10, "match": 0.5, "contribution": 5.0, "reason": "501c3 required; fiscal sponsor accepted as alternative"},
    {"name": "Amount Range", "weight": 5, "match": 1.0, "contribution": 5.0, "reason": "Range $10K-$50K overlaps target"}
  ],
  "raw_score": 25.0,
  "max_possible": 30.0,
  "fit_score": 8.33
}
```

### 3.2 Template Library (Replaces AI Drafter)

The Template Library provides pre-built paragraph templates that human users select, customize, and assemble into grant application responses.

#### 3.2.1 Template Structure

```python
class Template:
    id: UUID
    name: str                    # "Mission Alignment — Youth Development"
    category: str                # "Mission Alignment" | "Need Statement" | etc.
    focus_areas: list[str]       # Tags for filtering
    body: str                    # Template text with {{variable}} placeholders
    variables: list[str]         # Auto-filled from org profile: ["org_name", "program_name"]
    word_count_target: int       # Suggested word count for this section type
    is_custom: bool              # False = system template; True = user-created from past application
    version: int
```

#### 3.2.2 Template Categories

| Category | Description |
|----------|-------------|
| Mission Alignment | Why org's mission fits funder's priorities |
| Need Statement | Evidence of community need |
| Population Served | Description of target youth population |
| Program Description | What the specific program does |
| Evaluation Plan | How outcomes will be measured |
| Budget Narrative | How funds will be used |
| Sustainability Plan | How program continues after grant period |
| Organization Capacity | Why org is positioned to execute |
| Partnerships | Collaborators and relationships |
| Youth Voice | How youth are involved in program design |

#### 3.2.3 Variable Auto-Fill

When a user selects a template, placeholders are auto-populated from the organization profile:
- `{{org_name}}` → "Dojo at Somernova"
- `{{city}}` → "Somerville"
- `{{target_population}}` → "youth ages 12–22"
- User then edits the filled text for this specific grant

### 3.3 Structured Human Review Pipeline (Replaces AI Review Agents)

Four review checklists guide the human reviewer through a rigorous, structured process equivalent in rigor to AI-based review.

#### 3.3.1 Review 1 — Fact Verification Checklist

The user systematically verifies every factual claim.

Default checklist items (configurable):
- [ ] Every statistic cited has a named source document in the org library
- [ ] All program names match exactly those in the organization profile
- [ ] All dates, capacities, and counts are verifiable against org documents
- [ ] No program outcomes are claimed that are not documented
- [ ] All geographic references are accurate
- [ ] No staff titles or bios are misrepresented

#### 3.3.2 Review 2 — Assumption Log

User documents every assumption made in completing the application.

Structure per assumption:
- Description of the assumption
- Basis or rationale for the assumption
- Whether the assumption is documented in the application or left implicit

#### 3.3.3 Review 3 — Ambiguity Resolution Record

User documents every ambiguous instruction or term encountered.

Structure per ambiguity:
- Description of the ambiguous instruction or term
- Resolution approach (how the ambiguity was handled)
- Decision made

#### 3.3.4 Review 4 — Compliance Checklist

Default checklist items (auto-populated from grant requirements):
- [ ] All required narrative sections are completed
- [ ] Word/character limits are respected for each section
- [ ] All required attachments are prepared and listed
- [ ] Budget format matches funder requirements
- [ ] Application submitted by the correct entity (org vs. fiscal sponsor)
- [ ] All funder-specific questions are answered in full
- [ ] No prohibited content is included (if funder specifies restrictions)
- [ ] Content aligns with org's legal and ethics policies

### 3.4 Report Engine (Jinja2 — No AI)

The Report Engine generates the Weekly Grant Opportunities document from database data using Jinja2 templates.

#### 3.4.1 Template Structure

```
templates/reports/weekly_report.md.j2
  ├── Section 1: Executive Summary (counts, urgency breakdown, top 3)
  ├── Section 2: Ranked Grant Table (all grants, sorted by fit_score)
  ├── Section 3: Recommendation Memos (grants with fit_score >= 7)
  ├── Section 4: Application Checklists (grants with fit_score >= 7)
  └── Section 5: Relationship-Building Opportunities
```

#### 3.4.2 Data Passed to Template

```python
context = {
    "report_date": date.today(),
    "org": organization,
    "grants": grants_sorted_by_fit_score,
    "recommended": [g for g in grants if g.fit_score >= 7],
    "urgent": [g for g in grants if g.deadline_urgency == "RED"],
    "upcoming": [g for g in grants if g.deadline_urgency == "YELLOW"],
    "funders": funders_with_relationship_notes,
}
```

---

## 4. Database Design

### 4.1 Entity-Relationship Overview

```
Organization (1) ──────── has ────── (many) OrgDocuments
     │
     └── provides context for ─── SelectionCriteria (versioned)

Grant (many) ──────── belongs to ────── Funder (1)
   │
   └── has (0 or 1) ── Application
              │
              ├── has (many) ────── DraftVersion
              │       │
              │       └── has (4) ─── ReviewChecklist
              │                           │
              │               ├── has (many) ── ChecklistItem
              │               ├── has (many) ── AssumptionRecord
              │               └── has (many) ── AmbiguityRecord
              │
              ├── has (1) ────── Manifest
              └── has (many) ── DocumentRequirement

TemplateLibrary ──── contains ────── Template (many)

WeeklyReport (many) ──── summarizes ──── (many) Grants
```

### 4.2 Core Tables

#### `organizations`
| Column | Type | Notes |
|--------|------|-------|
| id | UUID PK | |
| name | VARCHAR(255) | |
| mission | TEXT | |
| values_text | TEXT | |
| programs_json | JSON | List of {name, description, focus_area} |
| eligibility_json | JSON | {has_501c3, fiscal_sponsor_name, target_geographies} |
| created_at | TIMESTAMP | |
| updated_at | TIMESTAMP | |

#### `org_documents`
| Column | Type | Notes |
|--------|------|-------|
| id | UUID PK | |
| org_id | UUID FK | |
| name | VARCHAR(255) | "IRS Determination Letter", "FY2026 Budget" |
| doc_type | VARCHAR(100) | legal, financial, program, bio, other |
| file_path | VARCHAR(1000) | Relative path in data/org_documents/ |
| year | INTEGER | Fiscal year if applicable |
| is_current | BOOLEAN | Is this the active version? |
| created_at | TIMESTAMP | |

#### `selection_criteria`
| Column | Type | Notes |
|--------|------|-------|
| id | UUID PK | |
| name | VARCHAR(255) | "Standard", "Climate-Focused" |
| version | VARCHAR(20) | |
| is_active | BOOLEAN | Only one active at a time |
| criteria_json | JSON | Array of {name, type, weight, is_hard_filter, config} |
| created_at | TIMESTAMP | |

#### `funders`
| Column | Type | Notes |
|--------|------|-------|
| id | UUID PK | |
| name | VARCHAR(255) | |
| website | VARCHAR(500) | |
| funder_type | ENUM | foundation, government, corporate, other |
| contact_json | JSON | {name, email, phone, address} |
| relationship_notes | TEXT | |
| total_awarded_usd | DECIMAL(12,2) | |
| created_at | TIMESTAMP | |
| updated_at | TIMESTAMP | |

#### `grants`
| Column | Type | Notes |
|--------|------|-------|
| id | UUID PK | |
| funder_id | UUID FK | |
| name | VARCHAR(500) | |
| description | TEXT | |
| amount_min | DECIMAL(12,2) | |
| amount_max | DECIMAL(12,2) | |
| deadline | DATE | NULL = rolling |
| deadline_urgency | ENUM | RED, YELLOW, GREEN, GRAY |
| eligibility_501c3_required | BOOLEAN | |
| fiscal_sponsorship_allowed | BOOLEAN | |
| geography | VARCHAR(500) | |
| focus_areas_json | JSON | List of focus area strings |
| fit_score | NUMERIC(4,2) | 0.00–10.00 |
| score_breakdown_json | JSON | Detailed criterion-level breakdown |
| scored_with_criteria_id | UUID FK | → selection_criteria |
| application_url | VARCHAR(1000) | |
| source_url | VARCHAR(1000) | Where user found this grant |
| status | ENUM | Lifecycle status (see Section 5.2) |
| notes | TEXT | Free-form user notes |
| is_deleted | BOOLEAN | Soft delete |
| created_at | TIMESTAMP | |
| updated_at | TIMESTAMP | |

#### `applications`
| Column | Type | Notes |
|--------|------|-------|
| id | UUID PK | |
| grant_id | UUID FK | (unique — one application per grant) |
| status | ENUM | Application lifecycle status |
| approved_by | VARCHAR(255) | |
| approved_at | TIMESTAMP | |
| submitted_at | TIMESTAMP | |
| submission_method | VARCHAR(255) | Online portal, email, mail, etc. |
| submission_confirmation | VARCHAR(500) | |
| outcome | ENUM | PENDING, AWARDED, REJECTED, WITHDRAWN |
| award_amount | DECIMAL(12,2) | |
| award_date | DATE | |
| outcome_notes | TEXT | |
| is_deleted | BOOLEAN | |
| created_at | TIMESTAMP | |
| updated_at | TIMESTAMP | |

#### `document_requirements`
| Column | Type | Notes |
|--------|------|-------|
| id | UUID PK | |
| application_id | UUID FK | |
| item | VARCHAR(500) | "IRS Determination Letter" |
| category | ENUM | required_doc, narrative_question, budget, reporting, contact |
| is_completed | BOOLEAN | |
| notes | TEXT | |

#### `draft_versions`
| Column | Type | Notes |
|--------|------|-------|
| id | UUID PK | |
| application_id | UUID FK | |
| version_number | VARCHAR(20) | "1.0", "1.1", "2.0" |
| sections_json | JSON | Array of {question, response, word_count, templates_used, is_template_derived} |
| total_word_count | INTEGER | |
| created_at | TIMESTAMP | |

#### `review_checklists`
| Column | Type | Notes |
|--------|------|-------|
| id | UUID PK | |
| application_id | UUID FK | |
| draft_version_id | UUID FK | |
| review_type | ENUM | fact_verification, assumption_log, ambiguity_resolution, compliance |
| status | ENUM | NOT_STARTED, IN_PROGRESS, COMPLETED, BLOCKED |
| completed_by | VARCHAR(255) | |
| completed_at | TIMESTAMP | |
| has_blocking_items | BOOLEAN | |
| created_at | TIMESTAMP | |

#### `checklist_items`
| Column | Type | Notes |
|--------|------|-------|
| id | UUID PK | |
| checklist_id | UUID FK | |
| item_text | TEXT | The checklist item description |
| is_checked | BOOLEAN | |
| is_critical | BOOLEAN | Unresolved critical items block advancement |
| finding | TEXT | User's finding or note |
| created_at | TIMESTAMP | |

#### `assumption_records`
| Column | Type | Notes |
|--------|------|-------|
| id | UUID PK | |
| checklist_id | UUID FK | (Review 2 checklist) |
| description | TEXT | What assumption was made |
| basis | TEXT | Rationale for the assumption |
| is_documented_in_draft | BOOLEAN | |
| created_at | TIMESTAMP | |

#### `ambiguity_records`
| Column | Type | Notes |
|--------|------|-------|
| id | UUID PK | |
| checklist_id | UUID FK | (Review 3 checklist) |
| description | TEXT | The ambiguous instruction or term |
| resolution_approach | TEXT | How it was handled |
| decision_made | TEXT | What was decided |
| created_at | TIMESTAMP | |

#### `manifests`
| Column | Type | Notes |
|--------|------|-------|
| id | UUID PK | |
| application_id | UUID FK | (1:1) |
| events_json | JSON | Append-only array of {timestamp, event_type, actor, details} |
| last_updated | TIMESTAMP | |

#### `templates`
| Column | Type | Notes |
|--------|------|-------|
| id | UUID PK | |
| name | VARCHAR(255) | |
| category | VARCHAR(100) | |
| focus_areas_json | JSON | Tags |
| body | TEXT | Template text with {{variable}} placeholders |
| variables_json | JSON | List of variable names used |
| word_count_target | INTEGER | |
| is_system | BOOLEAN | System-provided vs. user-created |
| version | INTEGER | |
| is_active | BOOLEAN | |
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

Streamlit selected for the same reasons as v1.0.0: pure Python, rapid development, built-in state management, sufficient for a single-org internal tool.

### 5.2 Navigation Structure

```
GMAS — Grants Manager Assistant System
├── 🏠 Dashboard                       (pages/01_dashboard.py)
├── ➕ Enter Grant                      (pages/02_enter_grant.py)
├── 📊 Grant Database                  (pages/03_grants.py)
├── 📋 Applications                    (pages/04_applications.py)
│   ├── Application Overview
│   ├── Draft Editor (Template Library)
│   └── Review Checklists (4 tabs)
├── 📝 Weekly Report                   (pages/05_reports.py)
├── 🤝 Funders                         (pages/06_funders.py)
├── 📈 Analytics                       (pages/07_analytics.py)
└── ⚙️  Settings                       (pages/08_settings.py)
    ├── Organization Profile
    ├── Selection Criteria Editor
    ├── Template Library Manager
    ├── Review Checklist Editor
    └── Integrations (Google Docs, Ollama)
```

### 5.3 Key Screens

**Dashboard**
- Pipeline summary: 5 metric cards (Grants Tracked, Recommended, Applications Active, Submissions Pending, Awarded This Year)
- Urgent deadlines widget (RED/YELLOW grants with days remaining)
- Recent activity feed (last 10 grant entries, status changes, reviews completed)
- Quick actions: "Add Grant" · "Generate Weekly Report" · "View Applications"

**Grant Database Page**
- Filters sidebar: urgency tier, status, focus area, amount range, fit score min, 501c3 required, fiscal ok
- Main table: Funder · Grant Name · Fit Score (bar) · Urgency (badge) · Deadline · Amount · Status
- Color-coded urgency: RED bg for urgent, YELLOW for upcoming
- Per-row actions: View · Edit · Create Application · Archive

**Application Detail Page (critical screen)**
- Header: grant name, funder, deadline urgency badge, amount
- Tabs: Overview · Document Checklist · Draft Editor · Reviews (4) · Manifest
- Draft Editor tab: version selector, template browser sidebar, rich-text draft area, word count
- Reviews tab: 4 sub-tabs (one per checklist), each with checklist items, findings notes, completion status
- Approval button: visually locked (grey, tooltip explains blockers) until all reviews complete + no critical items

**Settings → Selection Criteria Editor**
- Named rule sets with active toggle
- Per-criterion rows: name · type · weight slider · hard filter toggle
- Preview: test-score a hypothetical grant against current rules
- Save/activate buttons

**Settings → Template Library**
- Table of templates by category
- Inline editor for template body text
- Variable placeholder helper (inserts {{org_name}}, etc.)
- "Create from Past Application" wizard

---

## 6. Data Flow

### 6.1 Grant Entry and Scoring Flow

```
User enters grant (form or CSV import)
  → Validation (required fields, URL format, date format)
  → Deduplication check (name + funder match, URL match)
    → Duplicate found? → User prompted to confirm merge or skip
  → Grant stored (status: DISCOVERED)
  → Rules Engine auto-scores grant against active criteria
    → Hard filter check → fail → score 0, reason stored
    → Weighted scoring → score + breakdown stored
    → Deadline classifier → urgency flag stored
  → Status advanced to EVALUATED
  → If score ≥ 7 → status advanced to RECOMMENDED
  → Dashboard and grant list updated
```

### 6.2 Application Drafting Flow

```
User selects grant → "Create Application"
  → Application record created (status: APPROVED_TO_APPLY)
  → Document requirements checklist auto-populated
  → Manifest: event "APPLICATION_CREATED" appended
  → User opens Draft Editor
    → Selects template category → browses templates
    → Selects template → variables auto-filled from org profile
    → User edits filled text in draft area
    → Draft section saved
  → User completes all sections → "Save Draft v1.0"
    → DraftVersion record created
    → Manifest: "DRAFT_CREATED v1.0" appended
  → User proceeds to Reviews
```

### 6.3 Review and Approval Flow

```
User opens Reviews tab
  → Four checklist tabs displayed (NOT_STARTED)
  → User works through each checklist:
      Review 1 (Fact Verification): checks each item, adds findings
      Review 2 (Assumption Log): adds assumption records
      Review 3 (Ambiguity Resolution): adds ambiguity records
      Review 4 (Compliance): checks each item, adds findings
  → Each checklist marked COMPLETED when all items addressed
  → Any critical item unchecked → checklist = BLOCKED
  → Manifest updated after each checklist completion
  → All 4 checklists COMPLETED + no critical blockers?
      → Approval section unlocked
      → User reads pre-submission acknowledgment checklist
      → User enters their name, checks each acknowledgment item
      → "Approve Application" button activated
      → User clicks → SubmissionApproval record created
      → Status → APPROVED
      → Manifest: "APPROVED_FOR_SUBMISSION" appended
  → Application ready for manual submission
```

---

## 7. Optional Ollama Integration

### 7.1 What Ollama Provides

Ollama is a free, open-source tool that runs LLMs (Large Language Models) locally on the user's machine. When installed and running, it provides AI assistance at zero ongoing cost.

### 7.2 Enabled Features (When Ollama is Running)

| Feature | Where | What it does |
|---------|-------|-------------|
| Draft paragraph assist | Draft Editor | Suggests a custom paragraph given template + grant context |
| Grant summary | Grant Detail | Summarizes a long grant description into 3 bullet points |
| Search query suggestions | Enter Grant page | Suggests search terms for finding similar grants |
| Compliance check assist | Review 4 | Highlights potential compliance issues in draft text |

### 7.3 Integration Architecture

```python
class OllamaClient:
    BASE_URL = "http://localhost:11434"  # Default Ollama port

    def is_available(self) -> bool:
        # Simple HTTP health check — returns False if not running
        ...

    def generate(self, prompt: str, model: str = "llama3") -> str:
        # POST to /api/generate
        # Raises OllamaUnavailableError if not running
        ...
```

- All Ollama calls wrapped in feature flag: `if settings.ollama_enabled and ollama_client.is_available()`
- If Ollama unavailable → feature silently absent; no error shown to user
- Ollama responses are suggestions, not authoritative — always presented as "AI Suggestion (review before using)"

---

## 8. Security Design

### 8.1 No API Keys Required for Core System

The production system's core workflow requires zero API keys. No key management is needed for basic operation.

### 8.2 Optional Credentials Management

Optional integrations require credentials, managed as follows:
- Google OAuth credentials: stored as a JSON file in `data/google_credentials.json` (in `.gitignore`); path configured in `.env`
- Ollama: no credentials required; connects to localhost only

### 8.3 Data Protection

- All form inputs validated and length-limited before storage
- SQLAlchemy ORM used exclusively — no raw SQL string construction
- Soft deletes only — no permanent deletion of any grant or application records
- File uploads (org documents) restricted by extension; stored in `data/org_documents/`

### 8.4 Approval Gate (Code-Level Enforcement)

```python
def approve_application(db, application_id, approver_name):
    # Check 1: All 4 review checklists are COMPLETED for current draft version
    # Check 2: No checklist has has_blocking_items = True
    # If either fails → raise SubmissionBlockedError
    # If all pass → create approval record, advance status to APPROVED
```

The service layer enforces this independently of the UI. Even if the Streamlit UI state is bypassed, the service raises `SubmissionBlockedError`.

---

## 9. Performance Considerations

- Rules Engine scoring for 500 grants completes in < 5 seconds (pure Python arithmetic)
- Grant table uses pagination (50 rows default, configurable)
- Streamlit `@st.cache_data` applied to analytics aggregation queries
- Jinja2 report rendering completes in < 10 seconds for reports up to 50 grants
- SQLite is sufficient for single-user local deployment with up to 10,000 grant records

---

## 10. Error Handling and Logging

- All service methods wrapped in try/except with typed custom exceptions
- Python `logging` module writes to `logs/gmas_YYYY-MM-DD.log` (rotating, 10MB max, 5 backup files)
- Log levels: DEBUG (scoring breakdowns), INFO (user actions, status transitions), WARNING (soft failures), ERROR (hard failures)
- Streamlit `st.error()` displays user-friendly messages; full stack traces in log file only
- Optional Ollama failures are silent (feature disappears; no error in UI)

---

## 11. Third-Party Integrations

| Service | Purpose | Required | Authentication |
|---------|---------|----------|---------------|
| Ollama (localhost) | Optional local AI features | NO | None — localhost |
| Google Docs API | Optional report publishing | NO | User's OAuth2 JSON file |
| PyMuPDF / weasyprint | PDF export | YES (bundled) | None |

**No paid external APIs are required for any production operation.**

---

## 12. Development Process Architecture

This section documents how Claude Code multi-agent teams will build the system.

### 12.1 Parallel Development Tracks

| Track | Agent Focus | Key Deliverables |
|-------|------------|-----------------|
| A — Infrastructure | Database models, Alembic migrations, config, logging, seeding | `src/models/`, `src/db/`, `src/utils/` |
| B — UI | All 8 Streamlit pages, components, design system | `src/app/pages/`, `src/app/components/` |
| C — Business Logic | Rules Engine, scoring, state machine, template system, report generator | `src/engine/`, `src/services/`, `src/templates/` |
| D — Testing | pytest fixtures, unit tests, integration tests, hard gate tests | `tests/` |
| E — Documentation | User docs, technical docs, deployment guide, CHANGELOG | `docs/` |

Tracks A, B, C, D, E run in parallel. Integration testing (Track D) begins after Tracks A and C complete their first milestone.

---

## 13. Appendices

### 13.1 Technology Version Targets

| Component | Technology | Version |
|-----------|-----------|---------|
| Language | Python | 3.11+ |
| Web Framework | Streamlit | 1.35+ |
| ORM | SQLAlchemy | 2.0+ |
| Migrations | Alembic | 1.13+ |
| Template Engine | Jinja2 | 3.1+ |
| Data Processing | Pandas | 2.2+ |
| Visualization | Plotly | 5.20+ |
| Settings | pydantic-settings | 2.x |
| Testing | pytest | 8.x |
| Linting | ruff | 0.4+ |
| Type Checking | mypy | 1.10+ |
| PDF Export | weasyprint or pymupdf | latest |
| Optional | ollama-python | 0.3+ |

### 13.2 Application Lifecycle States

```
DISCOVERED → EVALUATED → RECOMMENDED → APPROVED_TO_APPLY
  → DRAFTING → IN_REVIEW → APPROVED → SUBMITTED
    → AWARDED | REJECTED | WITHDRAWN
```

### 13.3 What Changed from v1.0.0

| v1.0.0 Component | v1.1.0 Replacement | Reason |
|-----------------|-------------------|--------|
| Grant Scout Agent (Claude API) | Manual entry + CSV import | No paid AI in production |
| Grant Evaluator Agent (Claude API) | Rules Engine (weighted scoring) | No paid AI in production |
| Application Drafter Agent (Claude API) | Template Library + human editing | No paid AI in production |
| Hallucination Reviewer Agent | Review 1: Fact Verification Checklist | No paid AI in production |
| Assumption Auditor Agent | Review 2: Assumption Log | No paid AI in production |
| Ambiguity Resolver Agent | Review 3: Ambiguity Resolution Record | No paid AI in production |
| Compliance Checker Agent | Review 4: Compliance Checklist | No paid AI in production |
| agent_logs table | Removed (no agents in production) | No paid AI in production |
| Orchestrator | Removed | No agents to orchestrate |
| Weekly Search Cycle | Manual trigger for report generation | User does web research |

---

**Document Version**: 1.1.0 | 2026-06-19
**Template Based On**: 02_High_Level_Design_Template_GENERIC.md
