# Grants Manager Assistant System (GMAS) - Detailed Design Document

**Version**: 1.1.0
**Created**: 2026-06-19 15:29 EST
**Modified**: 2026-06-19 15:30 EST
**Change from v1.0.0**: All AI runtime components removed from production system. Agent classes, Anthropic SDK, and orchestrator replaced by Rules Engine, Template Library, Review Checklist Engine, and Report Generator. Ollama optional client added. All production modules now require zero external API dependencies.

**AI LLM Engine (Development Only)**: Claude Sonnet 4.6 — used to BUILD the system, not to RUN it.
**Tech Stack**: Python · Streamlit · SQLAlchemy · SQLite → PostgreSQL · Pandas · Plotly · Jinja2

---

## 1. Introduction

### 1.1 Purpose

This document provides module-level implementation specifications for GMAS v1.1.0. Every major design decision is made here so that a developer (or a Claude Code agent team) can implement each module without further design work.

### 1.2 Scope

All modules: database, models, engine, services, templates, UI pages, utilities, optional Ollama integration, testing, and deployment.

### 1.3 References

1. `01_PRD_v1.1.0.md`
2. `02_High_Level_Design_v1.1.0.md`

---

## 2. Module Designs

### 2.1 Database Module (`src/db/`)

#### 2.1.1 `database.py` — Engine and Session Factory

```python
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from src.utils.config import settings

engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False} if "sqlite" in settings.database_url else {},
    echo=settings.db_echo,
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

class Base(DeclarativeBase):
    pass

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    from src.models import *  # noqa: F401, F403 — imports all models for metadata registration
    Base.metadata.create_all(bind=engine)
```

#### 2.1.2 Alembic Configuration

- `
.ini` at project root — `sqlalchemy.url` reads from env
- `src/db/migrations/env.py` imports `Base.metadata` from `src.models`
- Pre-migration hook: copies `gmas.db` to `data/backups/gmas_pre_migrate_TIMESTAMP.db`
- Commands: `alembic upgrade head` (apply), `alembic downgrade -1` (rollback one)

#### 2.1.3 `seed_data.py` — Initial Data Seeder

Populates:
1. Organization record (Dojo at Somernova) with full mission/programs/values from workflow document
2. Default SelectionCriteria rule set ("Standard") with weights calibrated for Dojo's priorities
3. Default template library (15+ paragraph templates across all 10 categories)
4. Default review checklist item definitions for all 4 review types

---

### 2.2 Model Module (`src/models/`)

All models inherit from `Base`. All have `created_at`, `updated_at`, `is_deleted`. UUIDs generated client-side with `uuid.uuid4()`.

#### 2.2.1 `organization.py`

```python
class Organization(Base):
    __tablename__ = "organizations"
    id: Mapped[uuid.UUID] = mapped_column(UUID, primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    mission: Mapped[str] = mapped_column(Text, nullable=False)
    values_text: Mapped[str] = mapped_column(Text)
    programs_json: Mapped[list] = mapped_column(JSON, default=list)
    eligibility_json: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, onupdate=datetime.utcnow)
    documents: Mapped[list["OrgDocument"]] = relationship(back_populates="organization", lazy="select")
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

# Valid status transitions — enforced by state machine
VALID_TRANSITIONS: dict[GrantStatus, list[GrantStatus]] = {
    GrantStatus.DISCOVERED:       [GrantStatus.EVALUATED],
    GrantStatus.EVALUATED:        [GrantStatus.RECOMMENDED, GrantStatus.APPROVED_TO_APPLY],
    GrantStatus.RECOMMENDED:      [GrantStatus.APPROVED_TO_APPLY, GrantStatus.EVALUATED],
    GrantStatus.APPROVED_TO_APPLY:[GrantStatus.DRAFTING],
    GrantStatus.DRAFTING:         [GrantStatus.IN_REVIEW],
    GrantStatus.IN_REVIEW:        [GrantStatus.DRAFTING, GrantStatus.APPROVED],
    GrantStatus.APPROVED:         [GrantStatus.SUBMITTED, GrantStatus.IN_REVIEW],
    GrantStatus.SUBMITTED:        [GrantStatus.AWARDED, GrantStatus.REJECTED, GrantStatus.WITHDRAWN],
}

class Grant(Base):
    __tablename__ = "grants"
    # ... all columns per HLD Section 4.2
```

#### 2.2.3 All Other Models

Follow the same pattern. See HLD Section 4.2 for full column specifications. Model files:
- `funder.py` — Funder model
- `selection_criteria.py` — SelectionCriteria model
- `application.py` — Application, DocumentRequirement models
- `draft.py` — DraftVersion model
- `review.py` — ReviewChecklist, ChecklistItem, AssumptionRecord, AmbiguityRecord models
- `manifest.py` — Manifest model
- `template.py` — Template model
- `report.py` — WeeklyReport model
- `org_document.py` — OrgDocument model

---

### 2.3 Engine Module (`src/engine/`)

The engine module contains all deterministic intelligence — no AI, no external calls.

#### 2.3.1 `scoring_engine.py` — Rules-Based Fit Score Calculator

```python
from dataclasses import dataclass
from src.models.grant import Grant
from src.models.selection_criteria import SelectionCriteria

@dataclass
class CriterionResult:
    name: str
    weight: float
    match_value: float          # 0.0, 0.5, or 1.0
    contribution: float         # weight * match_value
    reason: str

@dataclass
class ScoreResult:
    fit_score: float            # 0.00–10.00
    hard_filter_failed: bool
    hard_filter_reason: str
    criteria_results: list[CriterionResult]
    raw_score: float
    max_possible: float
    criteria_id: str
    criteria_version: str

class ScoringEngine:
    def score_grant(self, grant: Grant, criteria: SelectionCriteria, org: Organization) -> ScoreResult:
        """
        Main scoring method. Returns a ScoreResult with full breakdown.
        """
        rules = criteria.criteria_json

        # Step 1: Hard filter evaluation
        for rule in [r for r in rules if r.get("is_hard_filter")]:
            match = self._evaluate_criterion(rule, grant, org)
            if match.match_value == 0.0:
                return ScoreResult(
                    fit_score=0.0,
                    hard_filter_failed=True,
                    hard_filter_reason=f"Hard filter failed: {rule['name']} — {match.reason}",
                    criteria_results=[match],
                    raw_score=0.0,
                    max_possible=sum(r["weight"] for r in rules),
                    criteria_id=str(criteria.id),
                    criteria_version=criteria.version,
                )

        # Step 2: Weighted scoring
        results = [self._evaluate_criterion(r, grant, org) for r in rules if not r.get("is_hard_filter")]
        raw_score = sum(r.contribution for r in results)
        max_possible = sum(r.weight for r in results)
        fit_score = (raw_score / max_possible * 10) if max_possible > 0 else 0.0

        return ScoreResult(
            fit_score=round(fit_score, 2),
            hard_filter_failed=False,
            hard_filter_reason="",
            criteria_results=results,
            raw_score=raw_score,
            max_possible=max_possible,
            criteria_id=str(criteria.id),
            criteria_version=criteria.version,
        )

    def _evaluate_criterion(self, rule: dict, grant: Grant, org: Organization) -> CriterionResult:
        """Dispatches to the appropriate evaluator by criterion type."""
        evaluator = {
            "geography": self._eval_geography,
            "focus_area": self._eval_focus_area,
            "eligibility": self._eval_eligibility,
            "amount_range": self._eval_amount_range,
        }.get(rule["type"], self._eval_unknown)
        return evaluator(rule, grant, org)

    def _eval_geography(self, rule, grant, org) -> CriterionResult:
        org_geographies = org.eligibility_json.get("target_geographies", [])
        grant_geo = grant.geography or ""
        match = any(geo.lower() in grant_geo.lower() for geo in org_geographies)
        return CriterionResult(
            name=rule["name"],
            weight=rule["weight"],
            match_value=1.0 if match else 0.0,
            contribution=rule["weight"] if match else 0.0,
            reason=f"{'Matches' if match else 'Does not match'} target geography ({', '.join(org_geographies)})",
        )

    # Similar implementations for _eval_focus_area, _eval_eligibility, _eval_amount_range
```

#### 2.3.2 `deadline_classifier.py`

```python
from datetime import date
from src.models.grant import DeadlineUrgency

def classify_urgency(deadline: date | None) -> DeadlineUrgency:
    if deadline is None:
        return DeadlineUrgency.GRAY
    days_remaining = (deadline - date.today()).days
    if days_remaining < 0:
        return DeadlineUrgency.GRAY     # Past deadline — treat as gray, not error
    elif days_remaining <= 30:
        return DeadlineUrgency.RED
    elif days_remaining <= 60:
        return DeadlineUrgency.YELLOW
    elif days_remaining <= 90:
        return DeadlineUrgency.GREEN
    return DeadlineUrgency.GRAY

def days_until_deadline(deadline: date | None) -> int | None:
    if deadline is None:
        return None
    return (deadline - date.today()).days
```

#### 2.3.3 `deduplication.py`

```python
from difflib import SequenceMatcher

def similarity(a: str, b: str) -> float:
    return SequenceMatcher(None, a.lower().strip(), b.lower().strip()).ratio()

def find_duplicates(candidate: dict, existing_grants: list[dict]) -> list[dict]:
    """
    Returns list of potential duplicates with match type.
    match_type: "exact" (definite) or "fuzzy" (possible, needs human review).
    """
    duplicates = []
    for existing in existing_grants:
        # Check 1: URL match
        if candidate.get("application_url") and candidate["application_url"] == existing.get("application_url"):
            duplicates.append({**existing, "match_type": "exact", "match_field": "application_url"})
            continue
        # Check 2: Exact name + funder match
        if (candidate.get("name", "").lower() == existing.get("name", "").lower() and
                candidate.get("funder_name", "").lower() == existing.get("funder_name", "").lower()):
            duplicates.append({**existing, "match_type": "exact", "match_field": "name+funder"})
            continue
        # Check 3: Fuzzy name match (same funder)
        if (candidate.get("funder_name", "").lower() == existing.get("funder_name", "").lower() and
                similarity(candidate.get("name", ""), existing.get("name", "")) > 0.85):
            duplicates.append({**existing, "match_type": "fuzzy", "match_field": "name_similarity"})
    return duplicates
```

#### 2.3.4 `state_machine.py`

```python
from src.models.grant import GrantStatus, VALID_TRANSITIONS
from src.utils.error_handler import InvalidStatusTransitionError

def advance_status(current: GrantStatus, new: GrantStatus) -> GrantStatus:
    allowed = VALID_TRANSITIONS.get(current, [])
    if new not in allowed:
        raise InvalidStatusTransitionError(
            f"Cannot transition from {current} to {new}. "
            f"Allowed transitions: {[s.value for s in allowed]}"
        )
    return new
```

#### 2.3.5 `template_renderer.py`

```python
import re

def render_template(body: str, context: dict) -> str:
    """
    Replaces {{variable}} placeholders with values from context dict.
    Unknown variables are left as-is (highlighted for user to fill in manually).
    """
    def replace(match):
        key = match.group(1).strip()
        return context.get(key, f"[FILL IN: {key}]")
    return re.sub(r'\{\{([^}]+)\}\}', replace, body)

def build_org_context(org: Organization) -> dict:
    return {
        "org_name": org.name,
        "city": org.eligibility_json.get("city", "Somerville"),
        "state": org.eligibility_json.get("state", "Massachusetts"),
        "mission": org.mission[:200],  # Short version for inline use
        "target_population": org.eligibility_json.get("target_population", "youth"),
        # ... other standard variables
    }
```

---

### 2.4 Service Module (`src/services/`)

#### 2.4.1 `grant_service.py`

```python
class GrantService:
    def __init__(self, db: Session, scoring_engine: ScoringEngine):
        self.db = db
        self.scoring = scoring_engine

    def create_grant(self, data: GrantCreateSchema) -> Grant:
        # 1. Validate input
        # 2. Deduplication check — raise DuplicateGrantError with matches if found
        # 3. Create Grant record (status: DISCOVERED)
        # 4. Auto-score with active criteria
        # 5. Classify deadline urgency
        # 6. Advance status to EVALUATED (or RECOMMENDED if score >= 7)
        # 7. Return grant
        ...

    def import_from_csv(self, file_path: str) -> dict:
        # Reads CSV, validates schema, calls create_grant for each row
        # Returns: {imported: N, duplicates: M, errors: [list of row errors]}
        ...

    def re_score_all(self, criteria_id: UUID) -> int:
        # Re-scores all non-terminal grants against specified criteria
        # Returns count of grants re-scored
        ...

    def get_grants_paginated(self, filters: GrantFilters, page: int, page_size: int = 50) -> Page[Grant]:
        ...

    def advance_status(self, grant_id: UUID, new_status: GrantStatus) -> Grant:
        grant = self.db.get(Grant, grant_id)
        grant.status = state_machine.advance_status(grant.status, new_status)
        self.db.commit()
        return grant

    def soft_delete(self, grant_id: UUID) -> None:
        grant = self.db.get(Grant, grant_id)
        grant.is_deleted = True
        self.db.commit()
```

#### 2.4.2 `application_service.py`

```python
class ApplicationService:
    def create_application(self, grant_id: UUID) -> Application:
        # Create Application, DocumentRequirement records, Manifest
        # Advance grant status to APPROVED_TO_APPLY
        ...

    def create_draft_version(self, application_id: UUID, sections: list[dict]) -> DraftVersion:
        # Version number auto-incremented
        # Manifest event appended
        ...

    def approve_application(self, application_id: UUID, approver_name: str) -> Application:
        """
        HARD GATE: raises SubmissionBlockedError if any condition fails.
        """
        app = self.db.get(Application, application_id)
        current_draft = self._get_current_draft(application_id)

        # Condition 1: All 4 review checklists are COMPLETED
        review_types = ["fact_verification", "assumption_log", "ambiguity_resolution", "compliance"]
        for review_type in review_types:
            checklist = self.db.query(ReviewChecklist).filter(
                ReviewChecklist.application_id == application_id,
                ReviewChecklist.draft_version_id == current_draft.id,
                ReviewChecklist.review_type == review_type,
                ReviewChecklist.status == "COMPLETED",
            ).first()
            if not checklist:
                raise SubmissionBlockedError(
                    f"Review checklist '{review_type}' is not complete. "
                    f"All four review checklists must be completed before approval."
                )

        # Condition 2: No checklist has blocking items
        blocking = self.db.query(ReviewChecklist).filter(
            ReviewChecklist.application_id == application_id,
            ReviewChecklist.draft_version_id == current_draft.id,
            ReviewChecklist.has_blocking_items == True,
        ).first()
        if blocking:
            raise SubmissionBlockedError(
                f"Checklist '{blocking.review_type}' has unresolved blocking items. "
                f"All blocking items must be resolved before approval."
            )

        # All conditions met — record approval
        app.approved_by = approver_name
        app.approved_at = datetime.utcnow()
        app.status = GrantStatus.APPROVED
        self.db.commit()
        self.manifest_service.append_event(application_id, "APPROVED", {"approver": approver_name})
        return app

    def record_submission(self, application_id: UUID, method: str, confirmation: str, submitter: str) -> Application:
        app = self.db.get(Application, application_id)
        if app.status != GrantStatus.APPROVED:
            raise SubmissionBlockedError("Application must be APPROVED before recording submission.")
        app.status = GrantStatus.SUBMITTED
        app.submitted_at = datetime.utcnow()
        app.submission_method = method
        app.submission_confirmation = confirmation
        self.db.commit()
        self.manifest_service.append_event(application_id, "SUBMITTED", {"method": method, "submitter": submitter})
        return app

    def record_outcome(self, application_id: UUID, outcome: str, award_amount: float = None) -> Application:
        ...
```

#### 2.4.3 `review_service.py`

```python
class ReviewService:
    def initialize_checklists(self, application_id: UUID, draft_version_id: UUID) -> list[ReviewChecklist]:
        """Creates 4 checklists for a new draft version, populating items from checklist definitions."""
        ...

    def update_checklist_item(self, item_id: UUID, is_checked: bool, finding: str = "") -> ChecklistItem:
        item = self.db.get(ChecklistItem, item_id)
        item.is_checked = is_checked
        item.finding = finding
        self.db.commit()
        # Update parent checklist blocking status
        self._update_checklist_status(item.checklist_id)
        return item

    def add_assumption(self, checklist_id: UUID, description: str, basis: str, is_documented: bool) -> AssumptionRecord:
        ...

    def add_ambiguity(self, checklist_id: UUID, description: str, resolution: str, decision: str) -> AmbiguityRecord:
        ...

    def complete_checklist(self, checklist_id: UUID, reviewer_name: str) -> ReviewChecklist:
        """Marks checklist COMPLETED if all items addressed and no unresolved critical items."""
        checklist = self.db.get(ReviewChecklist, checklist_id)
        blocking_items = self.db.query(ChecklistItem).filter(
            ChecklistItem.checklist_id == checklist_id,
            ChecklistItem.is_critical == True,
            ChecklistItem.is_checked == False,
        ).count()
        if blocking_items > 0:
            checklist.status = "BLOCKED"
            checklist.has_blocking_items = True
        else:
            checklist.status = "COMPLETED"
            checklist.has_blocking_items = False
            checklist.completed_by = reviewer_name
            checklist.completed_at = datetime.utcnow()
        self.db.commit()
        return checklist
```

#### 2.4.4 `report_service.py`

```python
from jinja2 import Environment, FileSystemLoader
import pandas as pd

class ReportService:
    def __init__(self, template_dir: str = "src/templates/reports"):
        self.jinja_env = Environment(loader=FileSystemLoader(template_dir))

    def generate_weekly_report(self, db: Session, org: Organization) -> WeeklyReport:
        """Generates weekly report from current DB state using Jinja2 template."""
        grants = db.query(Grant).filter(Grant.is_deleted == False).all()
        grants_sorted = sorted(grants, key=lambda g: g.fit_score, reverse=True)
        recommended = [g for g in grants_sorted if g.fit_score >= 7]
        funders = db.query(Funder).filter(Funder.is_deleted == False).all()

        context = {
            "report_date": date.today().isoformat(),
            "org": org,
            "grants": grants_sorted,
            "recommended": recommended,
            "urgent": [g for g in grants if g.deadline_urgency == "RED"],
            "upcoming": [g for g in grants if g.deadline_urgency == "YELLOW"],
            "pipeline": [g for g in grants if g.deadline_urgency == "GREEN"],
            "funders": funders,
            "total_count": len(grants),
            "urgent_count": sum(1 for g in grants if g.deadline_urgency == "RED"),
            "recommended_count": len(recommended),
        }

        template = self.jinja_env.get_template("weekly_report.md.j2")
        content = template.render(**context)

        report = WeeklyReport(content_markdown=content, ...)
        db.add(report)
        db.commit()
        return report

    def export_pdf(self, report: WeeklyReport, output_path: str) -> str:
        # Render Markdown to HTML, then HTML to PDF via weasyprint
        ...

    def publish_to_gdocs(self, report: WeeklyReport, folder_id: str) -> str:
        # Requires Google OAuth credentials — raises IntegrationDisabledError if not configured
        ...
```

#### 2.4.5 `manifest_service.py`

```python
class ManifestService:
    def create_manifest(self, db: Session, application_id: UUID) -> Manifest:
        manifest = Manifest(
            application_id=application_id,
            events_json=[],
        )
        db.add(manifest)
        db.commit()
        self.append_event(db, application_id, "APPLICATION_CREATED", {})
        return manifest

    def append_event(self, db: Session, application_id: UUID, event_type: str, details: dict) -> None:
        manifest = db.query(Manifest).filter(Manifest.application_id == application_id).first()
        event = {
            "timestamp": datetime.utcnow().isoformat(),
            "event_type": event_type,
            "details": details,
        }
        manifest.events_json = manifest.events_json + [event]  # Append-only
        manifest.last_updated = datetime.utcnow()
        db.commit()

    def export_markdown(self, db: Session, application_id: UUID) -> str:
        manifest = db.query(Manifest).filter(Manifest.application_id == application_id).first()
        lines = [f"# Application Manifest\n", f"**Application ID**: {application_id}\n\n", "## Event Log\n"]
        for event in manifest.events_json:
            lines.append(f"- **{event['timestamp']}** | `{event['event_type']}` | {event['details']}\n")
        return "".join(lines)
```

---

### 2.5 Streamlit UI Module (`src/app/`)

#### 2.5.1 `main.py`

```python
import streamlit as st

st.set_page_config(
    page_title="GMAS — Grants Manager",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS for urgency color coding and AI content badges
st.markdown("""<style>
    .urgency-red { background-color: #dc3545; color: white; padding: 2px 8px; border-radius: 4px; }
    .urgency-yellow { background-color: #ffc107; color: black; padding: 2px 8px; border-radius: 4px; }
    .urgency-green { background-color: #28a745; color: white; padding: 2px 8px; border-radius: 4px; }
    .urgency-gray { background-color: #6c757d; color: white; padding: 2px 8px; border-radius: 4px; }
    .template-fill { background-color: #e8f4fd; border-left: 3px solid #1f77b4; padding: 4px 8px; }
</style>""", unsafe_allow_html=True)
```

#### 2.5.2 Component Specifications

**`components/grant_card.py`**
```python
def render_grant_card(grant: Grant) -> None:
    """Renders a compact grant summary with urgency badge, fit score bar, and action buttons."""
    col1, col2, col3 = st.columns([3, 1, 1])
    with col1:
        st.markdown(f"**{grant.name}**")
        st.caption(f"{grant.funder.name} · {grant.geography}")
    with col2:
        st.progress(grant.fit_score / 10, text=f"Fit: {grant.fit_score:.1f}")
    with col3:
        urgency_html = f'<span class="urgency-{grant.deadline_urgency.lower()}">{grant.deadline_urgency}</span>'
        st.markdown(urgency_html, unsafe_allow_html=True)
```

**`components/review_status_panel.py`**
```python
def render_review_status(checklists: list[ReviewChecklist]) -> None:
    """4-column status display showing each review's completion status."""
    icons = {"COMPLETED": "✅", "IN_PROGRESS": "🔄", "NOT_STARTED": "⬜", "BLOCKED": "🚫"}
    labels = {
        "fact_verification": "1. Fact Check",
        "assumption_log": "2. Assumptions",
        "ambiguity_resolution": "3. Ambiguities",
        "compliance": "4. Compliance",
    }
    cols = st.columns(4)
    for i, checklist in enumerate(checklists):
        with cols[i]:
            st.metric(
                label=labels[checklist.review_type],
                value=icons[checklist.status],
                delta=f"{'BLOCKED' if checklist.has_blocking_items else checklist.status}",
            )
```

**`components/approval_gate.py`**
```python
def render_approval_gate(application: Application, checklists: list[ReviewChecklist]) -> None:
    """Shows approval button only when all pre-conditions are met. Otherwise shows blockers."""
    all_complete = all(c.status == "COMPLETED" for c in checklists)
    no_blockers = not any(c.has_blocking_items for c in checklists)

    if all_complete and no_blockers:
        st.success("All four reviews complete. Application is ready for approval.")
        approver = st.text_input("Your name (approver):")
        with st.expander("Pre-Submission Acknowledgment Checklist", expanded=True):
            ack1 = st.checkbox("I have reviewed all four checklist categories and found no critical issues.")
            ack2 = st.checkbox("I confirm this application represents the Dojo accurately and truthfully.")
            ack3 = st.checkbox("I understand submission must be done manually and cannot be automated by this system.")
        if approver and ack1 and ack2 and ack3:
            if st.button("✅ Approve Application for Submission", type="primary"):
                application_service.approve_application(application.id, approver)
                st.success(f"Application approved by {approver}. Status: APPROVED.")
                st.rerun()
    else:
        st.warning("Approval locked. Resolve the following before this application can be approved:")
        for c in checklists:
            if c.status != "COMPLETED":
                st.markdown(f"- **{c.review_type}**: {c.status}")
            elif c.has_blocking_items:
                st.markdown(f"- **{c.review_type}**: Has unresolved blocking items")
```

#### 2.5.3 Page Specifications

**`pages/01_dashboard.py`**
- 5 metric cards: Grants Tracked · Recommended · Applications Active · Awaiting Approval · Awarded This Year
- Urgency widget: table of RED/YELLOW grants with days remaining countdown
- Recent activity feed: last 10 status change events from manifests
- Quick actions: "Add Grant" · "Generate Report" · "View Recommended"

**`pages/02_enter_grant.py`**
- Two tabs: "Enter Manually" | "Import CSV"
- Manual form: all metadata fields with validation, focus area multi-select, URL fields
- CSV tab: file uploader, schema preview, column mapping UI, import button with progress
- Deduplication: if duplicates found, show side-by-side comparison before allowing save

**`pages/03_grants.py`**
- Sidebar filters panel
- Main sortable/filterable table (Streamlit dataframe with conditional row styling)
- Per-row action buttons: View · Edit · Create Application · Archive

**`pages/04_applications.py`**
- Application list view (default)
- Application detail view (on selection):
  - Five tabs: Overview · Documents · Draft Editor · Reviews · Manifest
  - Draft Editor: left sidebar with template browser, main area with section-by-section editor
  - Reviews: four sub-tabs with checklists, assumption/ambiguity record forms
  - Manifest: read-only timeline of all events

**`pages/05_reports.py`**
- "Generate Weekly Report" button with preview
- Historical reports list
- Download buttons (Markdown, PDF)
- Optional: "Publish to Google Docs" (shown only if Google integration is configured)

**`pages/08_settings.py`**
- Four tabs: Organization · Criteria · Templates · Integrations
- Criteria Editor: per-criterion rows with weight sliders, hard filter toggle, live score preview
- Template Library: table + inline editor + variable helper
- Integrations: Ollama status indicator + toggle, Google Docs OAuth setup

---

### 2.6 Optional AI Module (`src/optional_ai/`)

#### 2.6.1 `ollama_client.py`

```python
import httpx

class OllamaUnavailableError(Exception):
    pass

class OllamaClient:
    BASE_URL = "http://localhost:11434"

    def is_available(self) -> bool:
        try:
            response = httpx.get(f"{self.BASE_URL}/api/tags", timeout=2.0)
            return response.status_code == 200
        except Exception:
            return False

    def generate(self, prompt: str, model: str = "llama3", max_tokens: int = 500) -> str:
        if not self.is_available():
            raise OllamaUnavailableError("Ollama is not running on localhost:11434")
        response = httpx.post(
            f"{self.BASE_URL}/api/generate",
            json={"model": model, "prompt": prompt, "stream": False, "options": {"num_predict": max_tokens}},
            timeout=60.0,
        )
        response.raise_for_status()
        return response.json()["response"]

    def suggest_draft_paragraph(self, template_text: str, org_context: dict, grant_context: dict) -> str:
        """Generates a suggested paragraph based on a template and context."""
        prompt = f"""You are helping write a grant application paragraph for {org_context['org_name']}.

Template to adapt:
{template_text}

Organization context: {org_context['mission']}
Grant focus: {grant_context.get('description', '')}

Write a specific, factual paragraph based only on the provided context. Do not invent statistics or outcomes."""
        return self.generate(prompt)
```

All Ollama calls in the UI are wrapped:
```python
# Example usage pattern in Streamlit page
if settings.ollama_enabled:
    client = OllamaClient()
    if client.is_available():
        if st.button("🤖 Get AI Suggestion (Local Ollama)"):
            try:
                suggestion = client.suggest_draft_paragraph(template_text, org_context, grant_context)
                st.info(f"**AI Suggestion** (review and edit before using):\n\n{suggestion}")
            except OllamaUnavailableError:
                st.warning("Ollama is not responding. Suggestion unavailable.")
```

---

### 2.7 Utility Module (`src/utils/`)

#### 2.7.1 `config.py`

```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    database_url: str = "sqlite:///data/gmas.db"
    db_echo: bool = False
    log_level: str = "INFO"
    ollama_enabled: bool = False
    ollama_model: str = "llama3"
    google_docs_enabled: bool = False
    google_credentials_path: str = ""
    deadline_alert_days: int = 14
    recommended_score_threshold: float = 7.0
    page_size: int = 50

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()
```

`.env.example`:
```
# GMAS Configuration
# No paid AI API keys required for core operation

DATABASE_URL=sqlite:///data/gmas.db
DB_ECHO=false
LOG_LEVEL=INFO

# Optional: Local AI (Ollama — free, runs locally)
OLLAMA_ENABLED=false
OLLAMA_MODEL=llama3

# Optional: Google Docs integration (requires Google Cloud project)
GOOGLE_DOCS_ENABLED=false
GOOGLE_CREDENTIALS_PATH=

# Behavior settings
DEADLINE_ALERT_DAYS=14
RECOMMENDED_SCORE_THRESHOLD=7.0
```

#### 2.7.2 `logger.py`

```python
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
from src.utils.config import settings

def get_logger(name: str) -> logging.Logger:
    Path("logs").mkdir(exist_ok=True)
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, settings.log_level))
    if not logger.handlers:
        handler = RotatingFileHandler(
            f"logs/gmas_{date.today():%Y-%m-%d}.log",
            maxBytes=10_000_000,
            backupCount=5,
            encoding="utf-8",
        )
        handler.setFormatter(logging.Formatter(
            "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
            datefmt="%Y-%m-%dT%H:%M:%S",
        ))
        logger.addHandler(handler)
    return logger
```

#### 2.7.3 `error_handler.py`

```python
class GmasError(Exception):
    """Base exception for all GMAS errors."""

class SubmissionBlockedError(GmasError):
    """Raised when approval/submission is attempted without meeting all conditions."""

class InvalidStatusTransitionError(GmasError):
    """Raised when an invalid lifecycle status transition is attempted."""

class DuplicateGrantError(GmasError):
    """Raised when a potential duplicate grant is detected; includes matches."""
    def __init__(self, message: str, matches: list):
        super().__init__(message)
        self.matches = matches

class ValidationError(GmasError):
    """Raised for invalid input data."""

class IntegrationDisabledError(GmasError):
    """Raised when an optional integration is called but not configured."""

class OllamaUnavailableError(GmasError):
    """Raised when Ollama integration is called but Ollama is not running."""
```

---

## 3. Jinja2 Report Templates (`src/templates/`)

### 3.1 `reports/weekly_report.md.j2`

```jinja2
# Dojo Grant Opportunities — {{ report_date }}

## Section 1: Executive Summary

**Total Grants Tracked**: {{ total_count }}
**URGENT (≤30 days)**: {{ urgent_count }}
**UPCOMING (31–60 days)**: {{ upcoming_count }}
**Recommended (Score ≥ 7)**: {{ recommended_count }}

### Top 3 Recommended Grants

{% for grant in recommended[:3] %}
{{ loop.index }}. **{{ grant.name }}** — {{ grant.funder.name }}
   Fit Score: {{ grant.fit_score }}/10 · Deadline: {{ grant.deadline or "Rolling" }} · Amount: ${{ grant.amount_min|int }}–${{ grant.amount_max|int }}
{% endfor %}

## Section 2: Ranked Grant Table

| # | Grant | Funder | Fit Score | Urgency | Deadline | Amount Range |
|---|-------|--------|-----------|---------|----------|--------------|
{% for grant in grants %}
| {{ loop.index }} | {{ grant.name }} | {{ grant.funder.name }} | {{ grant.fit_score }} | {{ grant.deadline_urgency }} | {{ grant.deadline or "Rolling" }} | ${{ grant.amount_min|int }}–${{ grant.amount_max|int }} |
{% endfor %}

## Section 3: Recommendation Memos

{% for grant in recommended %}
### {{ grant.name }} — {{ grant.funder.name }}

**Deadline**: {{ grant.deadline or "Rolling" }} | **Urgency**: {{ grant.deadline_urgency }}
**Amount**: ${{ grant.amount_min|int }}–${{ grant.amount_max|int }}
**Fit Score**: {{ grant.fit_score }}/10

**Why it fits the Dojo**: {{ grant.score_breakdown_json.get('summary', 'Review score breakdown for details.') }}

**Application**: {{ grant.application_url }}

> Do not apply without team approval.

{% endfor %}

## Section 4: Application Checklists

{% for grant in recommended %}
### {{ grant.name }}

- [ ] Required documents prepared
- [ ] Narrative questions reviewed
- [ ] Budget template obtained
- [ ] Reporting requirements noted
- [ ] Funder contact identified: {{ grant.funder.contact_json.get('name', 'See funder website') }}

{% endfor %}

## Section 5: Relationship-Building Opportunities

{% for funder in funders %}
{% if funder.relationship_notes %}
**{{ funder.name }}**: {{ funder.relationship_notes }}
{% endif %}
{% endfor %}
```

---

## 4. Testing Strategy

### 4.1 Unit Tests (`tests/unit/`)

| Test File | What it Tests | Coverage Target |
|-----------|--------------|----------------|
| `test_scoring_engine.py` | All criterion types, hard filters, edge cases | 100% |
| `test_deadline_classifier.py` | All urgency tiers, null deadline, past deadline | 100% |
| `test_deduplication.py` | Exact name, URL match, fuzzy match, no match | 100% |
| `test_state_machine.py` | Valid transitions, invalid transitions | 100% |
| `test_template_renderer.py` | Variable replacement, unknown variables, empty context | 100% |
| `test_grant_service.py` | Create, update, soft delete, re-score | 90% |
| `test_application_service.py` | Create, approve (pass/fail gates), submit, outcome | 95% |
| `test_review_service.py` | All four checklists, blocking logic, completion | 90% |
| `test_report_service.py` | Template rendering, PDF export, section completeness | 85% |
| `test_manifest_service.py` | Create, append event, export | 90% |

### 4.2 Key Test Cases — Hard Gate Enforcement

```python
# tests/unit/test_application_service.py

def test_approve_fails_when_reviews_incomplete(db, sample_application):
    """Hard gate: approval blocked when not all checklists complete."""
    service = ApplicationService(db)
    with pytest.raises(SubmissionBlockedError, match="not complete"):
        service.approve_application(sample_application.id, "Test User")

def test_approve_fails_when_blocking_items_exist(db, sample_application_with_completed_reviews):
    """Hard gate: approval blocked when blocking checklist items exist."""
    # Mark one checklist as COMPLETED but with has_blocking_items=True
    checklist = db.query(ReviewChecklist).filter(...).first()
    checklist.has_blocking_items = True
    db.commit()
    service = ApplicationService(db)
    with pytest.raises(SubmissionBlockedError, match="blocking items"):
        service.approve_application(sample_application_with_completed_reviews.id, "Test User")

def test_approve_succeeds_when_all_conditions_met(db, sample_application_fully_reviewed):
    """Hard gate: approval succeeds only when all four checklists complete, no blockers."""
    service = ApplicationService(db)
    app = service.approve_application(sample_application_fully_reviewed.id, "Test Approver")
    assert app.status == GrantStatus.APPROVED
    assert app.approved_by == "Test Approver"
    assert app.approved_at is not None
```

### 4.3 Key Test Cases — Scoring Engine

```python
def test_hard_filter_blocks_scoring():
    engine = ScoringEngine()
    grant = mock_grant(geography="California")
    org = mock_org(target_geographies=["Massachusetts", "Greater Boston"])
    criteria = mock_criteria(hard_filters=["geography"])
    result = engine.score_grant(grant, criteria, org)
    assert result.fit_score == 0.0
    assert result.hard_filter_failed is True

def test_weighted_scoring_all_criteria_match():
    engine = ScoringEngine()
    # Grant matches all criteria
    result = engine.score_grant(...)
    assert result.fit_score == 10.0

def test_score_breakdown_stored_correctly():
    # Verify score_breakdown_json contains correct criterion-level details
    ...
```

### 4.4 Integration Tests (`tests/integration/`)

- `test_full_grant_lifecycle.py` — entry → scoring → application → review → approval → submission
- `test_csv_import.py` — valid CSV, invalid rows, duplicates handled
- `test_report_generation.py` — full weekly report rendered from seeded data
- `test_status_transitions.py` — all valid transitions pass, all invalid transitions raise error

### 4.5 Test Fixtures (`tests/conftest.py`)

```python
@pytest.fixture
def db():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        seed_test_data(session)  # Seeds org, criteria, templates
        yield session

@pytest.fixture
def sample_grant(db):
    # Returns a scored, evaluated Grant in EVALUATED status

@pytest.fixture
def sample_application_fully_reviewed(db, sample_grant):
    # Returns an Application with all 4 checklists COMPLETED and no blocking items
    # Hard gate should succeed on this fixture
```

---

## 5. Deployment

### 5.1 Local Development Setup

```bash
# Clone or unpack project
cd grants_assistant

# Create virtual environment (Python 3.11+)
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate    # macOS/Linux

# Install dependencies (NO Anthropic SDK — not needed for production)
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env if needed (all defaults work for local SQLite)

# Initialize database and seed data
alembic upgrade head
python src/db/seed_data.py

# Run the application
streamlit run src/app/main.py
```

Application available at: `http://localhost:8501`

### 5.2 `requirements.txt` (Production — No AI SDK)

```
streamlit>=1.35.0
sqlalchemy>=2.0.0
alembic>=1.13.0
pandas>=2.2.0
plotly>=5.20.0
jinja2>=3.1.0
pydantic-settings>=2.0.0
httpx>=0.27.0          # For optional Ollama client
weasyprint>=62.0       # For PDF export
python-dotenv>=1.0.0
pytest>=8.0.0
pytest-mock>=3.0.0
ruff>=0.4.0
mypy>=1.10.0
```

Note: `anthropic` SDK is NOT in `requirements.txt`. It is used only during development by Claude Code.

### 5.3 Docker

```dockerfile
FROM python:3.11-slim

# Install weasyprint system dependencies
RUN apt-get update && apt-get install -y \
    libpango-1.0-0 libpangoft2-1.0-0 libpangocairo-1.0-0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ src/
COPY alembic.ini .
COPY .env.example .env

RUN mkdir -p data/org_documents data/backups data/exports logs

EXPOSE 8501

CMD ["sh", "-c", "alembic upgrade head && python src/db/seed_data.py && streamlit run src/app/main.py --server.port=8501 --server.headless=true"]
```

### 5.4 Environment Variables (`.env.example`)

```
# No paid AI API keys required
DATABASE_URL=sqlite:///data/gmas.db
LOG_LEVEL=INFO
OLLAMA_ENABLED=false
GOOGLE_DOCS_ENABLED=false
DEADLINE_ALERT_DAYS=14
RECOMMENDED_SCORE_THRESHOLD=7.0
```

### 5.5 Cloud Deployment

| Platform | Method | Cost | PostgreSQL |
|----------|--------|------|-----------|
| Streamlit Community Cloud | Git push | Free | Not included — use SQLite |
| Railway.app | Docker | ~$5/mo | PostgreSQL add-on |
| Render.com | Docker | Free tier / $7/mo | PostgreSQL add-on |
| AWS ECS + RDS | Docker + Terraform | $15–30/mo | RDS PostgreSQL |

For cloud: set `DATABASE_URL=postgresql://...` in platform environment variables. Run `alembic upgrade head` as a release command.

---

## 6. Change Log

### Version 1.1.0 (2026-06-19)

- **REMOVED**: All AI agent classes (`BaseAgent`, `GrantScoutAgent`, `GrantEvaluatorAgent`, `ApplicationDrafterAgent`, all review agents, `Orchestrator`)
- **REMOVED**: `src/agents/` directory
- **REMOVED**: `anthropic` from `requirements.txt`
- **REMOVED**: `agent_logs` database table
- **ADDED**: `src/engine/scoring_engine.py` — deterministic weighted scoring with full criterion breakdown
- **ADDED**: `src/engine/deduplication.py` — fuzzy and exact duplicate detection
- **ADDED**: `src/engine/state_machine.py` — lifecycle transition enforcement
- **ADDED**: `src/engine/template_renderer.py` — Jinja2 variable substitution for paragraph templates
- **ADDED**: `templates/` module — paragraph template library and Jinja2 report templates
- **ADDED**: `src/optional_ai/ollama_client.py` — optional zero-cost local AI integration
- **CHANGED**: `application_service.approve_application()` hard gate now checks 4 human review checklists (not AI review reports)
- **CHANGED**: DB schema — added `review_checklists`, `checklist_items`, `assumption_records`, `ambiguity_records`, `templates`, `org_documents` tables
- **CHANGED**: `.env.example` — no API keys required; only optional feature flags

### Version 1.0.0 (2026-06-19)
- Initial version — superseded by v1.1.0.

---

**Document Version**: 1.1.0 | 2026-06-19
**Template Based On**: 03_Detailed_Design_Outline_Template_GENERIC.md
