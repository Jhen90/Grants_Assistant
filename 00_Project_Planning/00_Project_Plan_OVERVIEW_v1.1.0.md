# Grants Manager Assistant System - Project Overview

**Version**: 1.1.0
**Created**: 2026-06-19 15:29 EST
**Modified**: 2026-06-19 15:30 EST
**Change from v1.0.0**: Architectural correction — AI agents are development-process tools only. The production system requires NO paid AI services and runs with zero ongoing AI costs.

**AI LLM Engine (Development Only)**: Claude Sonnet 4.6 (claude-sonnet-4-6) — used to BUILD the system, not to RUN it.
**Tech Stack**: Python · Streamlit · SQLAlchemy · SQLite → PostgreSQL · Pandas · Plotly · Jinja2

---

## Project Name

**Grants Manager Assistant System (GMAS)**

---

## Project Description

The Grants Manager Assistant System solves the painful, expert-dependent, time-consuming lifecycle of grant fund-raising for the **Dojo at Somernova** — a youth-centered community program in Somerville, Massachusetts.

The system is a **traditional full-stack Python web application** — a structured, intelligent workflow tool that organizes every stage of the grants process: discovering and recording opportunities, evaluating and ranking them against configurable criteria, managing application workflows, guiding structured drafting with templates, enforcing a rigorous human review process, and tracking the full lifecycle from search to submission to award.

**No paid AI services are required to run the system.** The system is built with intelligence (rules engines, template libraries, structured checklists) but all of that intelligence runs locally without any API calls or subscription fees. Optional local AI assistance is available at zero cost via Ollama (a free, locally-run LLM tool).

**AI is used to BUILD the system, not to RUN it.** A multi-agent Claude Code development team will build the software in parallel, dramatically reducing development time and improving quality. This is a one-time development cost, not an ongoing operational expense.

---

## Problem Statement

> The grants finding, funding, and fulfillment process is **TEDIOUS, TIME-CONSUMING, DIFFICULT, and REQUIRES EXTREME EXPERTISE AND EXPERIENCE.** Good grants are scarce, have many logistic, relationship, or political hurdles, and mastering the process can take decades. Hidden barriers, varying agency requirements, deadline traps, and ambiguous instructions make it extraordinarily error-prone. Having an intelligent, structured process management system would make the process dramatically more efficient and successful.

---

## Solution Statement

GMAS is a **full-stack Python web application** that provides:

- A structured **grant repository** where opportunities are recorded, evaluated against configurable criteria, and ranked by fit score and deadline urgency
- A configurable **rules-based scoring engine** that calculates fit scores automatically from grant attributes vs. organizational criteria — no AI required
- A **template library** for application drafting that provides reusable paragraph templates organized by question type, supporting rapid human-driven drafting
- A **structured review pipeline** with four human-completed checklists (hallucinations, assumptions, ambiguities, compliance) that mirrors the rigor of an AI review without requiring AI
- A **hard approval gate** that enforces no submission without explicit human sign-off
- A **lifecycle tracker** and reporting dashboard covering the entire grants pipeline from discovery to award
- **Optional local AI assistance** via Ollama (free, local, no API key) for teams that want AI-assisted drafting without recurring costs

---

## Clarification: Two Separate Uses of "AI Agents"

This project involves AI in two completely different contexts. This distinction is critical:

| Context | What AI Does | When | Cost |
|---------|-------------|------|------|
| **Development Process** | Claude Code multi-agent teams write the application code, tests, and documentation | One-time, during development | One-time development cost |
| **Production System** | The running application — NO AI required | Ongoing, every day | **Zero ongoing AI cost** |

The v1.0.0 documents conflated these two roles. v1.1.0 separates them clearly.

---

## High-Level Solution Design

### System Development Process (SDLC)

1. **DEFINE** — PRD: Product Requirements Document
2. **DESIGN** — High-Level Design + Detailed Design Documents
3. **DEVELOP** — Phased implementation using parallel Claude Code agent teams
4. **TEST** — Unit, integration, and system-level testing
5. **DOCUMENT** — User and technical documentation
6. **DELIVER** — Local deployment first; cloud deployment as Phase 2

---

## Phased Requirements (MVP Approach)

### Phase 1 — Foundation (Core Data & UI)
1. Organization profile management (Dojo mission, values, programs, eligibility settings)
2. Grant repository with full CRUD
3. Manual grant entry with all metadata fields
4. Deadline urgency tracker with color-coded flags (RED/YELLOW/GREEN/GRAY)
5. Grant search, filter, and sort dashboard
6. Supporting documents library (IRS letter, budget, bios, program descriptions)

### Phase 2 — Rules-Based Intelligence
7. Configurable Selection Criteria and Rules Editor (geography, focus area, eligibility, amount range)
8. Weighted scoring engine — automatically calculates fit score from grant attributes vs. criteria
9. Hard filter rules — automatically exclude grants failing mandatory criteria
10. Urgency notification system (configurable threshold alerts)
11. Grant deduplication engine

### Phase 3 — Application Management
12. Application lifecycle state machine (full lifecycle from DISCOVERED to AWARDED)
13. Document requirements checklist per grant (auto-generated from grant metadata)
14. Application draft management with version history
15. Manifest document (audit trail) auto-generated for every application
16. Template Library — reusable paragraph templates organized by grant question type

### Phase 4 — Structured Human Review Pipeline
17. Four-category review checklist system:
    - Category 1: Fact Verification Checklist (replaces Hallucination Reviewer)
    - Category 2: Assumption Log (replaces Assumption Auditor)
    - Category 3: Ambiguity Resolution Record (replaces Ambiguity Resolver)
    - Category 4: Compliance Checklist (replaces Compliance Checker)
18. Per-checklist-item completion tracking
19. Blocking logic: uncompleted critical checklist items block advancement
20. Disambiguation records stored per application

### Phase 5 — Approval Gate and Submission
21. Multi-stage sign-off workflow
22. Hard approval gate (code-enforced — no submission without complete reviews + sign-off)
23. Pre-submission acknowledgment checklist (user confirms each item)
24. Submission logging and confirmation tracking
25. Post-submission outcome tracking (awarded/rejected/withdrawn/pending)

### Phase 6 — Reporting and Analytics
26. Weekly Grant Opportunities report (auto-generated from database, no AI)
27. Lifecycle pipeline dashboard (Kanban-style by status)
28. Analytics charts: win rate, funding by focus area, deadline adherence
29. Google Docs / Markdown / PDF export
30. Funder relationship management and engagement tracking

### Phase 7 — Optional Local AI Features (Zero Cost)
31. Ollama integration (optional, local LLM — llama3, mistral, etc.)
32. AI-assisted draft paragraph generation (if Ollama is running)
33. AI-assisted grant description summarization (if Ollama is running)
34. System fully functional without Ollama — it is an enhancement, never a requirement

### Phase 8 — Deployment and Operations
35. Docker containerization (local and cloud)
36. Cloud deployment options (Railway, Render, AWS, GCP)
37. CI/CD pipeline (GitHub Actions)
38. Automated database backup

---

## Solution Architecture

### Core Production Components (No AI Required)

#### 1. Organization Profile Module
- Dojo mission, values, programs, target population
- Eligibility settings (501c3 status, fiscal sponsorship, target geography)
- Supporting documents library

#### 2. Grant Repository Module
- Full grant metadata storage and retrieval
- Lifecycle status state machine
- Deduplication engine (name matching + URL matching)

#### 3. Rules-Based Scoring Engine
- Configurable criteria (geography, focus area, eligibility type, amount range)
- Weighted scoring calculation (no AI — pure arithmetic on grant attributes)
- Hard filter rules that auto-exclude ineligible grants
- Fit score = weighted sum of criterion matches (0.0–10.0)

#### 4. Template Library
- Pre-built paragraph templates for common grant question types (mission alignment, population served, program description, evaluation plan, budget narrative, etc.)
- User selects and customizes templates; system tracks versions
- Templates organized by focus area and question category

#### 5. Application Management Module
- Application lifecycle tracker
- Draft versioning system
- Document requirements checklist (auto-populated from grant metadata)
- Manifest / audit trail auto-generator

#### 6. Structured Review Pipeline
- Four human-completed review checklists per application draft
- Per-item completion tracking with notes
- Blocking logic for critical items
- Disambiguation record storage

#### 7. Approval and Submission Module
- Sign-off workflow engine
- Code-enforced hard gate (not just UI)
- Submission logging and outcome tracking

#### 8. Reporting and Dashboard Module
- Jinja2 template-based report generation from database
- Pipeline dashboard
- Analytics (Plotly charts)
- Google Docs / Markdown / PDF export

#### 9. Database Module
- SQLite (local MVP) → PostgreSQL (production)
- SQLAlchemy ORM + Alembic migrations

#### 10. Optional Local AI Module
- Ollama client (disabled by default)
- Feature-flag controlled — system fully works with it off
- No external API calls — runs entirely on local machine

---

## Multi-Agent Development Process

This section describes how **Claude Code AI agents** are used to **build** the system — not how the system runs in production.

### Development Team Structure

Five parallel Claude Code agent tracks build the system simultaneously:

```
Track A: Database & Infrastructure
  ├── SQLAlchemy models for all 10+ tables
  ├── Alembic migration scripts
  ├── Database seeding (org profile, templates)
  └── Config management, logging utilities

Track B: Streamlit UI
  ├── App structure, navigation, layout
  ├── All 8 pages (dashboard through settings)
  ├── Reusable components (cards, badges, forms)
  └── Design system, color palette

Track C: Business Logic Services
  ├── Scoring engine (weighted rules calculator)
  ├── Deadline classifier
  ├── Application state machine
  ├── Deduplication engine
  └── Report generator (Jinja2 templates)

Track D: Testing
  ├── pytest fixtures and conftest
  ├── Unit tests for all services
  ├── Integration tests for full workflows
  └── Hard gate enforcement tests

Track E: Documentation
  ├── User documentation (weekly cycle guide)
  ├── Technical documentation
  ├── Deployment guide
  └── CHANGELOG
```

Tracks A, B, C, D, and E run **in parallel** — a single Claude Code session orchestrates all five, with integration at Phase 3.

### Why This Approach Matters

Without parallel agent teams, building this system sequentially would take a developer 3–4 weeks. With parallel agent tracks managed by Claude Code, the same work is completed in **1–2 days of focused development sessions**, with consistent code quality, full test coverage, and complete documentation from day one.

---

## Technology Stack

### Production System (Required — No AI)

| Component | Technology | Purpose |
|-----------|-----------|---------|
| Web Framework | Streamlit 1.35+ | Primary UI |
| Database | SQLite → PostgreSQL | Data persistence |
| ORM | SQLAlchemy 2.x | Database abstraction |
| Migrations | Alembic 1.13+ | Schema versioning |
| Template Engine | Jinja2 | Report and document generation |
| Data Processing | Pandas 2.2+ | Analytics and aggregation |
| Visualization | Plotly 5.20+ | Charts and dashboards |
| Settings | pydantic-settings | Config and env management |
| Testing | pytest 8.x | Unit and integration tests |
| Code Quality | ruff, mypy | Linting and type checking |
| Containerization | Docker | Deployment packaging |

### Optional Local AI (Zero Cost, Not Required)

| Component | Technology | Purpose |
|-----------|-----------|---------|
| Local LLM | Ollama | Free local AI assistance (llama3, mistral) |
| Ollama SDK | ollama-python | Python client for local Ollama |

### Development Process Only (Not in Production)

| Component | Technology | Purpose |
|-----------|-----------|---------|
| AI Dev Tool | Claude Code | Builds the application code |
| AI Model | claude-sonnet-4-6 | Primary development model |
| Agent SDK | Anthropic SDK | Development-time code generation only |

---

## Project Folder Structure

```
Grants_Assistant/
├── 00_Project_Planning/          ← SDLC documents (this folder)
│   ├── 00_Project_Plan_OVERVIEW_v1.0.0.md  (superseded)
│   ├── 00_Project_Plan_OVERVIEW_v1.1.0.md  (current)
│   ├── 01_PRD_v1.0.0.md          (superseded)
│   ├── 01_PRD_v1.1.0.md          (current)
│   ├── 02_High_Level_Design_v1.0.0.md  (superseded)
│   ├── 02_High_Level_Design_v1.1.0.md  (current)
│   ├── 03_Detailed_Design_v1.0.0.md    (superseded)
│   └── 03_Detailed_Design_v1.1.0.md    (current)
│
├── SDLC_templates/               ← Template source files
│
├── src/                          ← All application source code
│   ├── app/                      ← Streamlit application
│   │   ├── pages/                ← Multi-page Streamlit UI (8 pages)
│   │   ├── components/           ← Reusable UI components
│   │   └── main.py               ← App entry point
│   │
│   ├── engine/                   ← Rules engine and core intelligence
│   │   ├── scoring_engine.py     ← Weighted criteria scoring
│   │   ├── deadline_classifier.py
│   │   ├── deduplication.py
│   │   └── state_machine.py      ← Application lifecycle
│   │
│   ├── templates/                ← Jinja2 and paragraph templates
│   │   ├── reports/              ← Weekly report templates
│   │   ├── drafts/               ← Paragraph template library
│   │   └── checklists/           ← Review checklist definitions
│   │
│   ├── models/                   ← SQLAlchemy ORM models
│   │   ├── grant.py
│   │   ├── application.py
│   │   ├── organization.py
│   │   ├── funder.py
│   │   ├── review.py
│   │   └── audit_log.py
│   │
│   ├── services/                 ← Business logic services
│   │   ├── grant_service.py
│   │   ├── scoring_service.py
│   │   ├── application_service.py
│   │   ├── review_service.py
│   │   ├── report_service.py
│   │   └── manifest_service.py
│   │
│   ├── db/                       ← Database setup
│   │   ├── database.py
│   │   └── migrations/           ← Alembic migrations
│   │
│   ├── optional_ai/              ← Optional local AI (Ollama only)
│   │   └── ollama_client.py      ← Feature-flagged; disabled by default
│   │
│   └── utils/                    ← Shared utilities
│       ├── logger.py
│       ├── config.py
│       ├── error_handler.py
│       └── export.py
│
├── tests/
│   ├── unit/
│   ├── integration/
│   └── conftest.py
│
├── data/
│   ├── org_documents/
│   └── exports/
│
├── .env.example
├── requirements.txt
├── pyproject.toml
├── alembic.ini
├── Dockerfile
└── README.md
```

---

## Development Timeline

| Phase | Duration | Key Deliverables | Parallel Tracks |
|-------|----------|-----------------|-----------------|
| 0 — Project Setup | 30 min | Repo, venv, structure, DB init | A |
| 1 — Foundation | 2–3 hrs | Grant DB, org profile, deadline tracker | A + B |
| 2 — Rules Engine | 2–3 hrs | Scoring engine, hard filters, dedup | C |
| 3 — Template Library | 2 hrs | Paragraph templates, review checklists | C + D |
| 4 — Application Mgmt | 3–4 hrs | Lifecycle, drafts, manifests | A + B + C |
| 5 — Review Pipeline | 2–3 hrs | 4 checklists, blocking logic | B + C |
| 6 — Approval & Submission | 2 hrs | Sign-off, hard gate, submission log | B + C |
| 7 — Reporting | 2–3 hrs | Dashboard, weekly report, analytics | B |
| 8 — Optional Ollama | 1–2 hrs | Feature-flagged local AI | C |
| 9 — Deployment | 2–3 hrs | Docker, cloud config, CI/CD | E |
| **Total** | **~20–25 hrs** | Full system | |

---

## Success Criteria

### Functional
- [ ] Grants are entered, scored by rules engine, and ranked by fit score — with no AI required
- [ ] All four review checklists are completable and tracked per application
- [ ] No application can advance to SUBMITTED without all checklists complete + human sign-off
- [ ] Weekly report document is auto-generated from database (no AI)
- [ ] System runs fully offline with zero external API dependencies
- [ ] Optional Ollama features work when Ollama is running, and are gracefully absent when not

### Technical
- [ ] Test coverage > 80%
- [ ] System starts and runs with only a Python environment — no API keys needed
- [ ] Clean Docker build for local and cloud deployment
- [ ] All scoring logic is deterministic and auditable (not AI black-box)

### Documentation
- [ ] PRD complete and approved
- [ ] High-Level Design complete
- [ ] Detailed Design complete
- [ ] User documentation (weekly cycle guide)
- [ ] Technical documentation
- [ ] Deployment guide

---

## SDLC Documentation Plan

| # | Document | Status |
|---|----------|--------|
| 00 | Project Plan Overview (this doc) | IN REVIEW |
| 01 | Product Requirements Document (PRD) | DRAFT |
| 02 | High-Level Design Document | DRAFT |
| 03 | Detailed Design Document | DRAFT |
| 04 | Implementation Plan | PENDING |
| 05 | Testing Plan | PENDING |
| 06 | User Documentation | PENDING |
| 07 | Technical Documentation | PENDING |
| 08 | Deployment Guide | PENDING |
| 09 | CHANGELOG | PENDING |

---

## Critical Rules (Non-Negotiable)

1. **NEVER submit a grant application without explicit human approval.** Enforced in code with a hard gate — not just a UI button.
2. **The production system MUST run without any paid AI API subscriptions.** Optional local AI (Ollama) is permitted; paid APIs are not required.
3. All scoring decisions must be deterministic and traceable to the configured criteria rules.
4. Every application must have a complete manifest (audit trail) document.
5. No draft content may be presented as fact — all templates and generated text must be reviewed by the user before submission.

---

## Change Log

### Version 1.1.0 (2026-06-19)
- **CRITICAL ARCHITECTURAL CHANGE**: Production system redesigned to require zero paid AI services.
- AI agents (Claude Code teams) are development-time tools only, not production runtime components.
- Replaced AI agent runtime architecture with: rules-based scoring engine, template library, structured human review checklists.
- Added optional Ollama (local LLM) integration as zero-cost AI option.
- Added clear separation section: "Two Separate Uses of AI Agents."

### Version 1.0.0 (2026-06-19)
- Initial version — superseded by v1.1.0.

---

**Document Version**: 1.1.0 | 2026-06-19
**Template Based On**: 00_Project_Plan_OVERVIEW_Template_GENERIC_v4.1.0.md
