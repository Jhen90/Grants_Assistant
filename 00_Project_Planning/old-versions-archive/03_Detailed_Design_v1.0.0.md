# Grants Manager Assistant System (GMAS) - Detailed Design Document

**Version**: 1.0.0
**Created**: 2026-06-19 15:29 EST
**Modified**: 2026-06-19 15:30 EST
**AI LLM Engine**: Claude Sonnet 4.6 (claude-sonnet-4-6)
**Tech Stack**: Python · Streamlit · SQLAlchemy · SQLite → PostgreSQL · Anthropic Claude API · Pandas · Plotly

---

## 1. Introduction

### 1.1 Purpose

This document specifies the module-level implementation design for GMAS. It provides enough detail for a developer (or Claude Code agent) to implement each module without further design decisions — all major choices are made here.

### 1.2 Scope

Covers all modules defined in the High-Level Design (HLD v1.0.0): database models, service classes, agent implementations, UI pages, utility modules, testing strategy, and deployment details.

### 1.3 References

1. `01_PRD_v1.0.0.md`
2. `02_High_Level_Design_v1.0.0.md`

---

## 2. Module Designs

### 2.1 Database Module (`src/db/`)

#### 2.1.1 `database.py` — Engine and Session Factory

```python
# Key responsibilities:
# - Create SQLAlchemy engine (SQLite for dev, PostgreSQL for prod)
# - Provide session factory (scoped_session or async session)
# - Expose get_db() dependency for service injection
# - Initialize tables on first run if they don't exist

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///data/gmas.db")
engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

class Base(DeclarativeBase):
    pass

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

#### 2.1.2 Alembic Configuration

- `alembic.ini` at project root
- `src/db/migrations/` holds all migration scripts
- `env.py` imports `Base.metadata` from models package
- Initial migration created with `alembic revision --autogenerate -m "initial schema"`
- SQLite backup created automatically before each migration via a custom Alembic hook

#### 2.1.3 Table Index Strategy

- `grants.deadline` — for deadline sorting and urgency queries
- `grants.fit_score` — for ranked list queries
- `grants.status` — for pipeline/Kanban views
- `applications.grant_id` — for application lookup by grant
- `agent_logs.created_at` — for log archival queries
- Composite: `(application_id, agent_id)` on `review_reports`

---

### 2.2 Model Module (`src/models/`)

Each file contains one or more SQLAlchemy `DeclarativeBase` subclasses.

#### 2.2.1 `organization.py`

```python
class Organization(Base):
    __tablename__ = "organizations"
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255))
    mission: Mapped[str] = mapped_column(Text)
    values_text: Mapped[str] = mapped_column(Text)
    programs_json: Mapped[dict] = mapped_column(JSON)
    eligibility_json: Mapped[dict] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(onupdate=datetime.utcnow)
    documents: Mapped[List["OrgDocument"]] = relationship(back_populates="organization")
```

#### 2.2.2 `grant.py`

```python
class GrantStatus(str, Enum):
    DISCOVERED = "DISCOVERED"
    EVALUATED = "EVALUATED"
    RECOMMENDED = "RECOMMENDED"
    APPROVED_TO_APPLY = "APPROVED_TO_APPLY"
    DRAFTING = "DRAFTING"
    IN_REVIEW = "IN_REVIEW"
    APPROVED = "APPROVED"
    SUBMITTED = "SUBMITTED"
    AWARDED = "AWARDED"
    REJECTED = "REJECTED"
    WITHDRAWN = "WITHDRAWN"

class DeadlineUrgency(str, Enum):
    RED = "RED"       # ≤30 days
    YELLOW = "YELLOW" # 31-60 days
    GREEN = "GREEN"   # 61-90 days
    GRAY = "GRAY"     # >90 days or rolling

class Grant(Base):
    __tablename__ = "grants"
    # ... all columns as defined in HLD Section 4.2
    application: Mapped[Optional["Application"]] = relationship(back_populates="grant")
    funder: Mapped["Funder"] = relationship(back_populates="grants")
```

#### 2.2.3 `application.py`

```python
class Application(Base):
    __tablename__ = "applications"
    # ... columns as defined in HLD
    draft_versions: Mapped[List["DraftVersion"]] = relationship(back_populates="application")
    review_reports: Mapped[List["ReviewReport"]] = relationship(back_populates="application")
    manifest: Mapped[Optional["Manifest"]] = relationship(back_populates="application", uselist=False)
```

All other models follow the same pattern — see HLD Section 4.2 for column specifications.

---

### 2.3 Agent Module (`src/agents/`)

#### 2.3.1 `base_agent.py` — Abstract Base Agent

```python
from anthropic import Anthropic
from dataclasses import dataclass

@dataclass
class AgentRequest:
    agent_id: str
    session_id: str
    org_context: dict
    target: dict
    extra_context: dict = field(default_factory=dict)

@dataclass
class AgentResponse:
    agent_id: str
    session_id: str
    status: str  # "success" | "error" | "partial"
    result: dict
    tokens_input: int
    tokens_output: int
    model: str
    generated_at: str

class BaseAgent:
    def __init__(self, client: Anthropic, model: str, prompt_version: str):
        self.client = client
        self.model = model
        self.prompt_version = prompt_version
        self._system_prompt = self._load_system_prompt()

    def _load_system_prompt(self) -> str:
        # Loads from src/agents/prompts/{agent_id}_v{version}.txt
        ...

    def _call_api(self, messages: list, tools: list = None) -> Message:
        # Wraps client.messages.create with retry logic (3 attempts, exponential backoff)
        ...

    def run(self, request: AgentRequest) -> AgentResponse:
        raise NotImplementedError
```

#### 2.3.2 `grant_scout.py` — Grant Scout Agent

**Responsibility**: Discover new grant opportunities via web search.

**System prompt key directives**:
- Search for grants matching each focus area in the workflow document
- Return structured JSON array of grant objects
- Include source URLs for all discovered grants
- Never fabricate grant information — only report what is found in search results

**Tool use**: Claude's `web_search` tool (or Tavily API via function tool definition)

**Input**: org context + active selection criteria + list of search queries
**Output**: Array of `{funder_name, grant_name, amount_min, amount_max, deadline, eligibility_..., application_url, source_url, description}`

**Execution**: Runs one search query per focus area (7 focus areas × configurable query variations = ~14 searches per weekly run)

#### 2.3.3 `grant_evaluator.py` — Grant Evaluator Agent

**Responsibility**: Score a single grant against selection criteria and produce a fit score + explanation.

**System prompt key directives**:
- Score 0–10 based on alignment with org mission, programs, target population, and values
- Apply hard filter rules first (if geography wrong → score 0 regardless)
- Write a 2–3 sentence explanation citing specific Dojo programs that align
- Be conservative — do not inflate scores

**Input**: org context + criteria rules/weights + single grant data
**Output**: `{fit_score: float, fit_explanation: str, hard_filter_failed: bool, hard_filter_reason: str}`

#### 2.3.4 `application_drafter.py` — Application Drafter Agent

**Responsibility**: Write compelling, factual narrative responses to each grant question.

**System prompt key directives**:
- Write ONLY from provided organizational context — no fabricated statistics, programs, or outcomes
- Frame responses around equity, youth voice, community safety, and economic mobility
- Flag any question where the org context is insufficient to answer fully
- Never invent testimonials, metrics, or case studies

**Input**: org context + supporting documents (text extracts) + grant questions array + grant context
**Output**: `{sections: [{question: str, response: str, word_count: int, confidence: float, flags: list}]}`

#### 2.3.5 Review Agent Suite (`src/agents/review_agents/`)

All review agents share a common pattern: they receive a complete draft and return a structured findings report.

**`hallucination_reviewer.py`**
- Checks every factual claim against the provided org context and grant source
- Returns: `{status: PASS|FAIL, findings: [{text: str, claim: str, traceable: bool, source: str}]}`

**`assumption_auditor.py`**
- Identifies all implicit assumptions in the draft
- Returns: `{status: PASS|WARNING, assumptions: [{assumption: str, documented: bool, basis: str}]}`

**`ambiguity_resolver.py`**
- Documents every ambiguous instruction or term in the grant application
- Returns: `{status: PASS|WARNING, ambiguities: [{description: str, resolution_approach: str, decision: str}]}`

**`compliance_checker.py`**
- Verifies all grant instructions are followed, all required fields present, legal/ethics alignment
- Returns: `{status: PASS|FAIL, checks: [{requirement: str, compliant: bool, issue: str}]}`

#### 2.3.6 `orchestrator.py` — Orchestrator

```python
class Orchestrator:
    def run_weekly_search(self, org_id: UUID, db: Session) -> WeeklySearchResult:
        # 1. Load org context + criteria
        # 2. Dispatch grant_scout (async)
        # 3. For each new grant: dispatch grant_evaluator (async, parallel)
        # 4. Store results, classify urgency
        # 5. Generate weekly report
        ...

    def run_application_draft(self, application_id: UUID, db: Session) -> DraftResult:
        # 1. Load org context + grant questions + doc library
        # 2. Dispatch app_drafter
        # 3. Store DraftVersion v1.0
        ...

    def run_review_pipeline(self, draft_version_id: UUID, db: Session) -> ReviewResult:
        # 1. Load draft content
        # 2. Dispatch 4 review agents (asyncio.gather for parallelism)
        # 3. Store 4 review reports
        # 4. Update manifest
        # 5. Return aggregated pass/fail status
        ...
```

---

### 2.4 Service Module (`src/services/`)

#### 2.4.1 `grant_service.py`

```python
class GrantService:
    def create_grant(self, db, data: dict) -> Grant: ...
    def update_grant(self, db, grant_id, data: dict) -> Grant: ...
    def get_grants(self, db, filters: dict, sort_by: str, page: int) -> Page[Grant]: ...
    def advance_status(self, db, grant_id, new_status: GrantStatus) -> Grant: ...
    def deduplicate(self, db, candidates: list[dict]) -> list[dict]: ...
```

#### 2.4.2 `scoring_service.py`

```python
class ScoringService:
    def classify_urgency(self, deadline: date) -> DeadlineUrgency: ...
    def apply_hard_filters(self, grant: dict, criteria: dict) -> tuple[bool, str]: ...
    def compute_fit_score(self, agent_score: float, criteria_weights: dict) -> float: ...
```

#### 2.4.3 `application_service.py`

```python
class ApplicationService:
    def create_application(self, db, grant_id: UUID) -> Application: ...
    def create_draft_version(self, db, application_id, sections: list) -> DraftVersion: ...
    def approve_application(self, db, application_id, approver: str) -> Application: ...
    def submit_application(self, db, application_id, confirmation: str) -> Application:
        # Hard gate: raises SubmissionBlockedError if:
        # - Not all 4 review agents returned PASS for current draft version
        # - No approval record exists
        ...
    def update_outcome(self, db, application_id, outcome: str, award_amount: float = None): ...
```

#### 2.4.4 `manifest_service.py`

```python
class ManifestService:
    def create_manifest(self, db, application_id: UUID) -> Manifest: ...
    def append_event(self, db, application_id, event_type: str, details: dict): ...
    def export_manifest(self, db, application_id) -> str: ...  # Returns Markdown
```

#### 2.4.5 `report_service.py`

```python
class ReportService:
    def generate_weekly_report(self, db, grants: list[Grant], org: Organization) -> str: ...
    def export_markdown(self, report: WeeklyReport) -> str: ...
    def publish_to_gdocs(self, report: WeeklyReport, folder_id: str) -> str: ...  # Returns doc URL
```

---

### 2.5 Streamlit UI Module (`src/app/`)

#### 2.5.1 `main.py` — Entry Point

```python
import streamlit as st

st.set_page_config(page_title="GMAS", page_icon="🎯", layout="wide")

pages = {
    "🏠 Dashboard": "pages/01_dashboard.py",
    "🔍 Grant Discovery": "pages/02_discovery.py",
    "📊 Grant Database": "pages/03_grants.py",
    "📋 Applications": "pages/04_applications.py",
    "📝 Weekly Report": "pages/05_reports.py",
    "🤝 Funders": "pages/06_funders.py",
    "📈 Analytics": "pages/07_analytics.py",
    "⚙️ Settings": "pages/08_settings.py",
}
```

#### 2.5.2 `components/` — Reusable Components

- `grant_card.py` — Grant summary card with urgency badge and fit score
- `review_status_panel.py` — 4-agent review status display with PASS/FAIL badges
- `approval_gate.py` — Sign-off form with hard-gate logic check before rendering
- `agent_progress.py` — Real-time progress display for running agent tasks
- `ai_content_badge.py` — Visual indicator for AI-generated content sections

#### 2.5.3 Page Specifications

**`pages/01_dashboard.py`**
- Top row: 4 metric cards (Total Grants, Urgent Deadlines, Recommended, Applications In Progress)
- Middle row: Urgency pipeline chart (Plotly bar) + Recent Activity feed
- Bottom row: Top 5 Recommended Grants table + Quick Actions

**`pages/02_discovery.py`**
- "Run Weekly Grant Search" button (triggers Orchestrator.run_weekly_search via background thread)
- Progress display while agents run
- Manual grant entry form (all metadata fields)
- Search session history table

**`pages/03_grants.py`**
- Filters sidebar: urgency, status, focus area, amount range, fit score min
- Main table with color-coded urgency badges, fit score bar
- Click-through to grant detail / edit form
- Bulk actions: archive, approve to apply

**`pages/04_applications.py`**
- Application list with status badges
- Application detail view:
  - Grant metadata header
  - Document checklist accordion
  - Draft version selector + rich text editor
  - "Generate Draft" button (triggers Drafter Agent)
  - "Send to Review" button (triggers Review Pipeline)
  - Review Status Panel (4 review agents)
  - Ambiguity Records accordion
  - Manifest / Audit Trail accordion
  - Approval Gate (disabled until all reviews PASS)

---

### 2.6 Utility Module (`src/utils/`)

#### 2.6.1 `logger.py`

```python
import logging
from logging.handlers import RotatingFileHandler

def get_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    handler = RotatingFileHandler(
        f"logs/gmas_{date.today()}.log",
        maxBytes=10_000_000,  # 10MB
        backupCount=5
    )
    handler.setFormatter(logging.Formatter(
        "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
    ))
    logger.addHandler(handler)
    return logger
```

#### 2.6.2 `config.py`

```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    anthropic_api_key: str
    tavily_api_key: str = ""
    database_url: str = "sqlite:///data/gmas.db"
    ai_model_primary: str = "claude-sonnet-4-6"
    ai_model_review: str = "claude-opus-4-8"
    google_docs_enabled: bool = False
    google_credentials_path: str = ""

    class Config:
        env_file = ".env"

settings = Settings()
```

#### 2.6.3 `error_handler.py`

```python
class GmasError(Exception):
    """Base exception for all GMAS errors."""

class AgentError(GmasError):
    """Raised when an AI agent call fails after all retries."""

class SubmissionBlockedError(GmasError):
    """Raised when application cannot be submitted (approval gate)."""

class DeduplicationError(GmasError):
    """Raised when a duplicate grant is detected."""

class ValidationError(GmasError):
    """Raised for invalid input data."""
```

#### 2.6.4 `export.py`

```python
def to_markdown(content: dict, template: str) -> str: ...
def to_pdf(markdown_content: str, output_path: str) -> str: ...
def to_docx(sections: list, output_path: str) -> str: ...
```

---

## 3. System Prompt Templates (`src/agents/prompts/`)

Each agent's system prompt is stored as a versioned text file:

```
src/agents/prompts/
├── grant_scout_v1.0.0.txt
├── grant_evaluator_v1.0.0.txt
├── application_drafter_v1.0.0.txt
├── hallucination_reviewer_v1.0.0.txt
├── assumption_auditor_v1.0.0.txt
├── ambiguity_resolver_v1.0.0.txt
└── compliance_checker_v1.0.0.txt
```

Prompt files include variable placeholders (`{{org_mission}}`, `{{criteria_rules}}`, etc.) filled by the agent at runtime from the database.

---

## 4. Database Schema — Full Column Specifications

See HLD Section 4.2 for all table definitions. Additional constraints:

- All `id` columns use UUID v4 (`uuid.uuid4()` default)
- All `_json` columns store Python dicts/lists serialized as JSON
- `fit_score` is stored as `NUMERIC(4,2)` to preserve precision
- `cost_usd` in `agent_logs` is `NUMERIC(8,4)` — 4 decimal places for API cost accuracy
- All datetimes stored as UTC

---

## 5. Data Processing Algorithms

### 5.1 Deadline Urgency Classification

```python
def classify_urgency(deadline: date | None) -> DeadlineUrgency:
    if deadline is None:
        return DeadlineUrgency.GRAY  # Rolling deadline
    days_remaining = (deadline - date.today()).days
    if days_remaining <= 30:
        return DeadlineUrgency.RED
    elif days_remaining <= 60:
        return DeadlineUrgency.YELLOW
    elif days_remaining <= 90:
        return DeadlineUrgency.GREEN
    return DeadlineUrgency.GRAY
```

### 5.2 Grant Deduplication

Match candidates against existing grants using:
1. Exact match on `(funder_name, grant_name)` — definite duplicate
2. Fuzzy match (Levenshtein distance < 0.15) on `grant_name` + same `funder_name` — flag for human review
3. URL match on `application_url` — definite duplicate

### 5.3 Weekly Report Generation

```python
def generate_weekly_report(grants: list[Grant], org: Organization) -> str:
    # Section 1: Executive Summary (counts by urgency, top 3 picks)
    # Section 2: Ranked Grant Table (all grants, sorted by fit_score desc)
    # Section 3: Recommendation Memos (score >= 7, full memo per grant)
    # Section 4: Application Checklists (score >= 7, checklist per grant)
    # Section 5: Relationship-Building Opportunities (funders to cultivate)
    # Returns: formatted Markdown string
```

---

## 6. Error Handling and Logging

### 6.1 Exception Hierarchy

```
GmasError
├── AgentError
│   ├── AgentTimeoutError
│   └── AgentResponseValidationError
├── SubmissionBlockedError
├── DeduplicationError
└── ValidationError
    ├── InputValidationError
    └── SchemaValidationError
```

### 6.2 Agent Retry Logic

```python
import asyncio

async def _call_with_retry(fn, *args, max_retries=3):
    for attempt in range(max_retries):
        try:
            return await fn(*args)
        except (APITimeoutError, RateLimitError) as e:
            if attempt == max_retries - 1:
                raise AgentError(f"Agent failed after {max_retries} attempts") from e
            await asyncio.sleep(2 ** attempt)  # 2s, 4s, 8s
```

### 6.3 Log Strategy

- **DEBUG**: Full agent prompts/responses (toggle with `LOG_LEVEL=DEBUG`)
- **INFO**: User actions, agent completions, status transitions
- **WARNING**: Soft failures (duplicate grant found, agent returned partial result)
- **ERROR**: Hard failures (agent max retries exceeded, DB error, submission blocked)

---

## 7. Testing Strategy

### 7.1 Unit Tests (`tests/unit/`)

| Module | Test File | Coverage Target |
|--------|-----------|----------------|
| `scoring_service.py` | `test_scoring_service.py` | 100% |
| `deadline_service.py` | `test_deadline_service.py` | 100% |
| `grant_service.py` | `test_grant_service.py` | 90% |
| `application_service.py` | `test_application_service.py` | 95% |
| `manifest_service.py` | `test_manifest_service.py` | 90% |
| `report_service.py` | `test_report_service.py` | 85% |
| `export.py` | `test_export.py` | 85% |

### 7.2 Integration Tests (`tests/integration/`)

- `test_grant_lifecycle.py` — full grant from DISCOVERED to SUBMITTED
- `test_application_review_pipeline.py` — full draft through 4 review agents (mocked agents)
- `test_submission_hard_gate.py` — verify SubmissionBlockedError raised without approval
- `test_deduplication.py` — verify duplicate detection across all three match strategies

### 7.3 Agent Tests (`tests/agents/`)

- All agent tests use mocked Anthropic SDK responses (`pytest-mock`)
- `test_agent_retry.py` — verify 3-attempt retry with exponential backoff
- `test_agent_response_validation.py` — verify malformed responses raise `AgentResponseValidationError`
- `test_orchestrator_weekly_cycle.py` — verify full weekly search cycle with mocked agents

### 7.4 Test Fixtures (`tests/conftest.py`)

```python
@pytest.fixture
def db():
    # In-memory SQLite for tests
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        yield session

@pytest.fixture
def mock_anthropic(mocker):
    return mocker.patch("src.agents.base_agent.Anthropic")

@pytest.fixture
def sample_org(db):
    # Returns seeded Organization record for tests
```

---

## 8. Deployment Details

### 8.1 Local Development Setup

```bash
# 1. Clone repo
git clone <repo_url>
cd grants_assistant

# 2. Create virtual environment
python -m venv .venv
.venv\Scripts\activate  # Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment
cp .env.example .env
# Edit .env: add ANTHROPIC_API_KEY, TAVILY_API_KEY

# 5. Initialize database
alembic upgrade head

# 6. Seed organization profile
python src/db/seed_org.py

# 7. Run app
streamlit run src/app/main.py
```

### 8.2 Docker (Local Container)

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY src/ src/
COPY alembic.ini .
EXPOSE 8501
CMD ["streamlit", "run", "src/app/main.py", "--server.port=8501"]
```

### 8.3 Cloud Deployment Options

| Platform | Method | Notes |
|----------|--------|-------|
| Streamlit Community Cloud | Git push | Free tier; secrets via Streamlit secrets |
| Railway.app | Docker | Simple PaaS; PostgreSQL add-on available |
| Render.com | Docker | Free tier with sleep; PostgreSQL add-on |
| AWS (ECS + RDS) | Docker + Terraform | Production-grade; full control |
| GCP (Cloud Run + Cloud SQL) | Docker | Serverless scaling; PostgreSQL |

### 8.4 Environment Variables Required

```
ANTHROPIC_API_KEY=sk-ant-...
TAVILY_API_KEY=tvly-...                    # For web search
DATABASE_URL=sqlite:///data/gmas.db        # Or PostgreSQL URL for cloud
AI_MODEL_PRIMARY=claude-sonnet-4-6
AI_MODEL_REVIEW=claude-opus-4-8
LOG_LEVEL=INFO
GOOGLE_DOCS_ENABLED=false                  # Set true + add credentials for GDocs
GOOGLE_CREDENTIALS_PATH=                   # Path to OAuth credentials JSON
```

### 8.5 Backup Strategy

- SQLite: Daily file copy to `data/backups/gmas_YYYY-MM-DD.db`
- PostgreSQL: Daily `pg_dump` to `data/backups/`
- Alembic: Automatic backup of SQLite before each `alembic upgrade`
- Backups retained for 30 days

---

## 9. Security Considerations

### 9.1 Input Validation

All form inputs validated using Pydantic models before reaching service layer. Max lengths enforced:
- URLs: 1000 chars
- Text fields: 50,000 chars
- Name fields: 255 chars

### 9.2 SQL Injection Prevention

- Exclusive use of SQLAlchemy ORM for all database operations
- Zero raw SQL strings in application code
- Parameterized queries only

### 9.3 API Key Protection

- Keys loaded from `.env` via `pydantic-settings`
- Keys masked in Settings page display (show only last 4 chars)
- `.env` in `.gitignore` — never committed
- Agent logs store prompt hashes, never raw API keys

### 9.4 Approval Gate — Code Implementation

```python
def submit_application(self, db, application_id: UUID, confirmation: str) -> Application:
    app = db.get(Application, application_id)

    # Check 1: All 4 review agents passed for current draft version
    current_draft = self._get_current_draft(db, application_id)
    review_agents = ["hallucination_reviewer", "assumption_auditor",
                     "ambiguity_resolver", "compliance_checker"]
    for agent_id in review_agents:
        report = db.query(ReviewReport).filter(
            ReviewReport.application_id == application_id,
            ReviewReport.draft_version_id == current_draft.id,
            ReviewReport.agent_id == agent_id,
            ReviewReport.status == "PASS"
        ).first()
        if not report:
            raise SubmissionBlockedError(
                f"Review not passed by {agent_id}. Submission blocked."
            )

    # Check 2: Human approval record exists
    if not app.approved_by or not app.approved_at:
        raise SubmissionBlockedError(
            "No human approval recorded. Submission blocked."
        )

    # All checks passed — log submission
    app.status = GrantStatus.SUBMITTED
    app.submitted_at = datetime.utcnow()
    app.submission_confirmation = confirmation
    db.commit()
    self.manifest_service.append_event(db, application_id, "SUBMITTED", {...})
    return app
```

---

## 10. Change Log

### Version 1.0.0 (2026-06-19)

- Initial Detailed Design created from HLD v1.0.0 and PRD v1.0.0.
- Adapted from Detailed Design Outline Template v4.0.0.

---

**Document Version**: 1.0.0 | 2026-06-19
**Template Based On**: 03_Detailed_Design_Outline_Template_GENERIC.md
