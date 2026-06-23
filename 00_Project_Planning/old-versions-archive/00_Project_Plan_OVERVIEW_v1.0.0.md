# Grants Manager Assistant System - Project Overview

**Version**: 1.0.0
**Created**: 2026-06-19 15:29 EST
**Modified**: 2026-06-19 15:30 EST
**AI LLM Engine**: Claude Sonnet 4.6 (claude-sonnet-4-6)
**Tech Stack**: Python · Streamlit · FastAPI · SQLAlchemy · SQLite → PostgreSQL · Anthropic Claude API · Pandas · Plotly

---

## Project Name

**Grants Manager Assistant System (GMAS)**

---

## Project Description

The Grants Manager Assistant System solves the painful, expert-dependent, time-consuming lifecycle of grant fund-raising for the **Dojo at Somernova** — a youth-centered community program in Somerville, Massachusetts. The process today requires deep institutional expertise to discover good grant opportunities, navigate varying agency requirements, avoid hidden traps, draft compelling applications, and track everything from discovery through award.

GMAS replaces that fragile, human-only process with an AI-orchestrated system that handles every stage: discovering grants, evaluating and ranking them against configurable criteria, managing application workflows, drafting narratives, performing multi-stage AI review, and tracking the full lifecycle from search to submission to award. It runs fully locally at first, with a clean path to cloud deployment.

---

## Problem Statement

> The grants finding, funding, and fulfillment process is **TEDIOUS, TIME-CONSUMING, DIFFICULT, and REQUIRES EXTREME EXPERTISE AND EXPERIENCE.** Good grants are scarce, have many logistic, relationship, or political hurdles, and mastering the process can take decades. Hidden barriers, varying agency requirements, deadline traps, and ambiguous instructions make it extraordinarily error-prone. Having intelligent assistants, analysts, and process managers would make the process dramatically more efficient and successful.

---

## Solution Statement

GMAS is a **full-stack Python web application** backed by an **orchestrated multi-agent AI team** (built on the Anthropic Claude API) that:

- **Discovers** grant opportunities automatically via AI-powered web research
- **Evaluates** each grant against configurable selection criteria and eligibility rules
- **Ranks** opportunities by fit score and deadline urgency
- **Manages** the application lifecycle end-to-end with full audit trails
- **Drafts** compelling, factual application narratives using organizational context
- **Reviews** every draft for hallucinations, assumption violations, ambiguities, and instruction compliance
- **Tracks** all submissions, approvals, relationships, and outcomes
- **Reports** on the entire process with dashboards and weekly summaries

The system enforces a hard rule: **no application is submitted without explicit human approval.**

---

## High-Level Solution Design

### System Development Process (SDLC)

1. **DEFINE** — PRD: Product Requirements Document
2. **DESIGN** — High-Level Design + Detailed Design Documents
3. **DEVELOP** — Phased implementation with parallel agent teams
4. **TEST** — Unit, integration, and system-level testing
5. **DOCUMENT** — User and technical documentation
6. **DELIVER** — Local deployment first; cloud deployment as Phase 2

---

## Phased Requirements (MVP Approach)

### Phase 1 — Foundation (Core Data & UI)
1. Organization profile management (Dojo context, mission, values, programs)
2. Grant repository with full CRUD (create, read, update, delete)
3. Manual grant entry with all metadata fields
4. Deadline urgency tracker with color-coded flags
5. Grant search/filter/sort dashboard

### Phase 2 — AI Intelligence Layer
6. Configurable Selection Criteria and Rules Editor
7. AI-powered grant discovery via web research (Grant Scout Agent)
8. Automated fit scoring and ranking (Grant Evaluator Agent)
9. Weekly Grant Opportunities report generation
10. Funder and relationship tracking

### Phase 3 — Application Management
11. Application lifecycle state machine (discovered → evaluating → approved → drafting → reviewing → approved → submitted → tracked)
12. Document requirements checklist per grant
13. Application draft management with version history
14. Manifest document (audit trail) auto-generation
15. Supporting documents library

### Phase 4 — AI Drafting & Review Pipeline
16. AI Application Drafter Agent (section-by-section narrative generation)
17. Hallucination Detector Review Agent
18. Assumption Auditor Review Agent
19. Ambiguity Resolver (disambiguation records per application)
20. Instruction Compliance Checker Agent
21. Legal/Ethics Alignment Checker Agent
22. Field Validation Agent

### Phase 5 — Approval & Submission
23. Multi-stage sign-off workflow
24. Final approval gate (hard block on submission without approval)
25. Submission logging and confirmation tracking
26. Post-submission status tracking (award/rejection/pending)

### Phase 6 — Reporting & Integration
27. Lifecycle dashboard with pipeline view
28. Google Docs export for weekly reports
29. Analytics (win rate, funding totals, funder relationship maps)
30. Scheduled weekly automated search runs

### Phase 7 — Deployment & Operations
31. Docker containerization
32. Cloud deployment (configurable: AWS / GCP / Azure)
33. CI/CD pipeline
34. Backup and disaster recovery

---

## Solution Architecture

### Core Components

#### 1. Organization Profile Module
- Dojo mission, values, programs, target population
- Eligibility settings (501c3 status, fiscal sponsorship, geography)
- Supporting documents library (IRS letter, budget, bios, program descriptions)

#### 2. Grant Repository Module
- Full grant metadata storage and retrieval
- Status lifecycle state machine
- Deadline urgency classification engine
- Deduplication and update tracking

#### 3. Selection Criteria Engine
- Configurable rules (geography, eligibility, focus areas, amount range)
- Scoring rubric editor
- Fit score calculation pipeline

#### 4. AI Agent Orchestrator
The heart of the system — coordinates five specialized AI agents:

| Agent | Role |
|-------|------|
| **Grant Scout Agent** | Web-searches for new grant opportunities each week |
| **Grant Evaluator Agent** | Scores each grant against criteria, produces ranked list |
| **Application Drafter Agent** | Writes narrative sections using org context + grant prompts |
| **Review Agent Suite** | Hallucination detection, assumption audit, compliance check, ambiguity resolution |
| **Orchestrator** | Dispatches agents, manages sequencing and parallelism, stores results |

#### 5. Application Management Module
- Application lifecycle tracker
- Draft versioning system
- Manifest / audit trail document generator
- Ambiguity resolution record system

#### 6. Review Pipeline Module
- Multi-stage review workflow
- Per-review checklists (hallucinations, assumptions, compliance, legal/ethics, field validation)
- Review status rollup
- Blocker escalation

#### 7. Approval & Submission Module
- Sign-off workflow engine
- Hard approval gate
- Submission logging
- Outcome tracking

#### 8. Reporting & Dashboard Module
- Weekly Grant Opportunities document
- Pipeline dashboard (Kanban-style)
- Analytics charts (Plotly)
- Google Docs / Markdown export

#### 9. Database Module
- SQLite (local MVP) → PostgreSQL (production)
- SQLAlchemy ORM + Alembic migrations
- Full audit log of all AI actions

#### 10. Utility Modules
- Structured logging with timestamps
- Error handling with graceful degradation
- Configuration management (`.env` / config file)
- Caching layer for AI results

---

## Technology Stack

| Component | Technology | Purpose |
|-----------|-----------|---------|
| Web Framework | Streamlit | Primary UI — rapid, Python-native |
| API Layer | FastAPI | Background tasks, agent endpoints |
| Database | SQLite → PostgreSQL | Data persistence |
| ORM | SQLAlchemy 2.x | Database abstraction |
| Migrations | Alembic | Schema versioning |
| Data Processing | Pandas | Analytics and report generation |
| Visualization | Plotly / Plotly Express | Charts and dashboards |
| AI Engine | Anthropic Claude API | All intelligent agent capabilities |
| AI Model (primary) | claude-sonnet-4-6 | Cost-effective, high-quality generation |
| AI Model (review) | claude-opus-4-8 | Maximum quality for review agents |
| Web Search | Claude built-in / Tavily API | Grant discovery research |
| Export | python-docx / markdown | Document generation |
| Google Docs | Google Docs API (v2) | Optional report publishing |
| Environment | Python 3.11+ / venv | Runtime |
| Version Control | Git | Source control |
| Testing | pytest | Unit and integration tests |
| Code Quality | black, ruff, mypy | Linting and type checking |
| Containerization | Docker | Deployment packaging |

---

## Multi-Agent Team Development Strategy

The **implementation itself** will use parallel Claude agent teams to accelerate delivery:

### Parallel Development Tracks

```
Track A: Foundation & Infrastructure
  └── Database schema, SQLAlchemy models, Alembic migrations, config

Track B: UI Shell & Navigation
  └── Streamlit app structure, page routing, layout, design system

Track C: AI Agent Framework
  └── Agent base classes, Claude API wrapper, orchestrator logic

Track D: Business Logic Services
  └── Scoring engine, deadline classifier, state machine, search logic

Track E: SDLC Documentation
  └── PRD, HLD, Detailed Design, Test Plan (running in parallel)
```

Tracks A, B, C, D, and E run **in parallel** during Phase 1-2. Integration happens at Phase 3.

### Agent Specialization in Production System

```
Weekly Run Cycle:
  1. Orchestrator triggers Grant Scout Agent (web research)
       ↓ parallel ↓
  2a. Grant Evaluator Agent scores new grants
  2b. Duplicate checker runs against existing DB
       ↓
  3. Ranked list → Weekly Report generated
       ↓ (on user request) ↓
  4. Application Drafter Agent writes sections
       ↓ parallel ↓
  5a. Hallucination Reviewer Agent
  5b. Compliance Checker Agent
  5c. Assumption Auditor Agent
  5d. Ambiguity Resolver Agent
       ↓ (all reviews pass) ↓
  6. Human sign-off required
       ↓
  7. Submission logged
```

---

## Development Timeline

| Phase | Duration | Key Deliverables | Parallel Tracks |
|-------|----------|-----------------|-----------------|
| 0 — Setup | 30 min | Repo, venv, folder structure, DB init | A |
| 1 — Foundation | 2-3 hrs | Grant DB CRUD, org profile, deadline tracker | A + B |
| 2 — AI Intelligence | 3-4 hrs | Scout agent, evaluator agent, scoring engine | C + D |
| 3 — Application Mgmt | 3-4 hrs | Lifecycle tracker, drafts, manifests | A + B + D |
| 4 — AI Drafting & Review | 4-5 hrs | Drafter agent, 4 review agents, ambiguity records | C + D |
| 5 — Approval & Submission | 2 hrs | Sign-off workflow, hard gate, submission log | B + D |
| 6 — Reporting | 2-3 hrs | Dashboard, weekly report, analytics, export | B |
| 7 — Deployment | 2-3 hrs | Docker, cloud config, CI/CD | E |
| **Total** | **~20-25 hrs** | Full system | |

---

## Project Folder Structure

```
Grants_Assistant/
├── 00_Project_Planning/          ← SDLC documents (this folder)
│   ├── 00_Project_Plan_OVERVIEW_v1.0.0.md
│   ├── 01_PRD_v1.0.0.md
│   ├── 02_High_Level_Design_v1.0.0.md
│   └── 03_Detailed_Design_v1.0.0.md
│
├── SDLS_templates/               ← Template source files
│
├── src/                          ← All application source code
│   ├── app/                      ← Streamlit application
│   │   ├── pages/                ← Multi-page Streamlit UI
│   │   ├── components/           ← Reusable UI components
│   │   └── main.py               ← App entry point
│   │
│   ├── agents/                   ← AI agent implementations
│   │   ├── base_agent.py         ← Base agent class
│   │   ├── orchestrator.py       ← Orchestrator agent
│   │   ├── grant_scout.py        ← Discovery agent
│   │   ├── grant_evaluator.py    ← Scoring agent
│   │   ├── application_drafter.py ← Drafting agent
│   │   └── review_agents/        ← Review agent suite
│   │       ├── hallucination_reviewer.py
│   │       ├── compliance_checker.py
│   │       ├── assumption_auditor.py
│   │       └── ambiguity_resolver.py
│   │
│   ├── models/                   ← SQLAlchemy ORM models
│   │   ├── grant.py
│   │   ├── application.py
│   │   ├── organization.py
│   │   ├── funder.py
│   │   ├── review.py
│   │   └── audit_log.py
│   │
│   ├── services/                 ← Business logic
│   │   ├── grant_service.py
│   │   ├── scoring_service.py
│   │   ├── deadline_service.py
│   │   ├── application_service.py
│   │   ├── review_service.py
│   │   └── report_service.py
│   │
│   ├── db/                       ← Database setup
│   │   ├── database.py           ← Engine, session factory
│   │   └── migrations/           ← Alembic migrations
│   │
│   └── utils/                    ← Shared utilities
│       ├── logger.py
│       ├── config.py
│       ├── error_handler.py
│       └── export.py
│
├── tests/                        ← pytest test suite
│   ├── unit/
│   ├── integration/
│   └── conftest.py
│
├── data/                         ← Local data files
│   ├── org_documents/            ← IRS letter, budget, bios, etc.
│   └── exports/                  ← Generated reports
│
├── .env.example                  ← Environment variable template
├── requirements.txt
├── pyproject.toml
├── alembic.ini
├── Dockerfile
└── README.md
```

---

## Success Criteria

### Functional
- [ ] Grant discovery agent finds and stores new grants each week
- [ ] Grants are scored and ranked against configurable criteria
- [ ] Deadline urgency flags (RED/YELLOW/GREEN/WHITE) are accurate
- [ ] Application drafts are generated from grant prompts + org context
- [ ] All four review agents produce structured review reports
- [ ] No application can be submitted without explicit sign-off
- [ ] Weekly report document is generated in Markdown and optionally Google Docs
- [ ] Full audit trail (manifest) exists for every application

### Technical
- [ ] Test coverage > 80%
- [ ] All AI responses stored and auditable in the database
- [ ] System runs fully locally with zero external dependencies beyond API keys
- [ ] Clean Docker build for local and cloud deployment
- [ ] Alembic migrations keep schema in sync

### Documentation
- [ ] PRD complete and approved
- [ ] High-Level Design document complete
- [ ] Detailed Design document complete
- [ ] User documentation (how to run weekly cycle)
- [ ] Technical documentation (developer reference)
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

1. **NEVER submit a grant application without explicit human approval.** The system must enforce this with a hard gate in code and workflow.
2. All AI-generated content must be flagged as AI-generated and reviewed before use.
3. All assumptions made by AI agents must be logged in a disambiguation record.
4. Every application must have a complete manifest (audit trail) document.
5. No grant-specific information is to be hallucinated — all content must trace back to org profile or grant source documents.

---

## Next Steps

1. **Review and approve** this Project Overview document
2. Create detailed PRD (`01_PRD_v1.0.0.md`)
3. Create High-Level Design (`02_High_Level_Design_v1.0.0.md`)
4. Create Detailed Design (`03_Detailed_Design_v1.0.0.md`)
5. Set up development environment and repository structure
6. Begin Phase 0 → Phase 1 implementation

---

**Document Version**: 1.0.0 | 2026-06-19
**Template Based On**: 00_Project_Plan_OVERVIEW_Template_GENERIC_v4.1.0.md
