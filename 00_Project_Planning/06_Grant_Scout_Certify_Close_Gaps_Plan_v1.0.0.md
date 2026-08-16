# Grant Scout — Certify & Close-Gaps Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Source spec:** `00_Project_Planning/Scout-Agent-Task-Plan-v1.1.0.md` (§3 RTM, gaps G1–G3; §4 tasks T1–T3; §6 review).

**Goal:** Close the three coverage gaps (G1 no-paid-AI guard, G2 queue-label unit test, G3 seed-scoring guard) test-first, then certify the whole Scout diff with a code review — turning the RTM to zero ❌/🟡 without adding features.

**Architecture:** Three additive, independent TDD tasks on the existing `feat/grantnova-scout` branch. T1 is a pure guard test (AST scan of the discovery import graph + Candid default-off assertion). T2 extracts the inline `_queue_label` from the Streamlit page into a pure, importable helper (`src/discovery/queue_label.py`) and unit-tests it. T3 guards the seeded `DEFAULT_CRITERIA` by running it through the real `ScoringEngine` via `evaluate_candidate`, asserting a matching grant scores > 0 and a hard-filtered one is INELIGIBLE. A final code-review pass (Task 4) certifies the branch.

**Tech Stack:** Python 3.11, pytest, SQLAlchemy (models only — no DB hit in these tests), Streamlit (page import only), Jinja2 (untouched). Deterministic, offline, no network.

## Global Constraints

_Every task's requirements implicitly include this section._

- **Runtime:** Python 3.11 in the `gmas` conda env. Run tests with
  `conda run -n gmas python -m pytest ...` from the repo root
  `c:\Users\jhenn\OneDrive\Desktop\01_Projects\Grants_Assistant`.
- **No paid AI, ever, in the discovery path** (NFR-SCOUT-002). Deterministic rules only.
- **No real DB, no network in tests** (NFR-SCOUT-005). Use in-memory objects / `SimpleNamespace` fakes; never open `grantnova.db`.
- **Scoring math is owned by `src/engine/scoring_engine.py`.** Do not duplicate or re-implement scoring; reuse `evaluate_candidate` / `ScoringEngine`.
- **Criteria `config` schema (verbatim keys the engine reads):** `type` (`geography|focus_area|eligibility|amount_range`), `weight` (int), `is_hard_filter` (bool), `config.target_geographies` (list), `config.target_focus_areas` (list), `config.min_acceptable` / `config.max_acceptable` (numbers).
- **Strong-match rule (from `evaluator.py`):** `is_strong_match = fit_score >= settings.recommendation_threshold (7.0) AND eligibility == ELIGIBLE`; `act_now = is_strong_match AND urgency in ("RED","YELLOW")`.
- **Commit cadence:** one commit per task (per-WP). End every commit body with
  `Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>`.
- **Gate after each task:** full suite ≥ 174 passing, re-run by the orchestrator.
- **Log any autonomous decision** (e.g. a real seed fix in T3) to
  `00_Project_Planning/DISAMBIGUATION_RECORD_v1.0.md` as D-025+.

**Baseline verification (run once before Task 1):**

Run: `conda run -n gmas python -m pytest -q`
Expected: `174 passed` (green baseline). If not green, stop and reconcile before starting.

---

### Task 1: Guard "no paid AI" (G1 / NFR-SCOUT-002)

**Files:**
- Create: `tests/unit/test_no_paid_ai.py`
- Test: (this file is the test)

**Interfaces:**
- Consumes: `src.discovery.sources.aggregator.CandidApiSource` (has `enabled` property reading `settings.candid_api_enabled and settings.candid_api_key`, both falsy by default).
- Produces: nothing consumed by later tasks. Pure guard.

**Why this shape:** the invariant already holds (there is no paid-AI import today, and Candid is off by default), so the "red" is proven by a *guard-has-teeth* test that feeds a synthetic `import openai` string to the same detector and asserts it is caught. The two real assertions then lock the invariant in place.

- [ ] **Step 1: Write the failing test**

Create `tests/unit/test_no_paid_ai.py`:

```python
# ============================================================
# File: tests/unit/test_no_paid_ai.py
# Description: Guards NFR-SCOUT-002 — the Grant Scout discovery path must stay
#   deterministic and free of any paid / hosted-LLM SDK, and the Candid API
#   source must remain OFF unless a key is explicitly configured.
# ============================================================

from __future__ import annotations

import ast
from pathlib import Path

from src.discovery.sources.aggregator import CandidApiSource

# Repo root: tests/unit/ -> tests/ -> <root>
PROJECT_ROOT = Path(__file__).resolve().parents[2]

# Paid / hosted-LLM SDKs the ToS-compliant deterministic path must never import.
BANNED_MODULES = {
    "openai",
    "anthropic",
    "cohere",
    "mistralai",
    "litellm",
    "replicate",
    "google.generativeai",
    "vertexai",
}

# The full Grant Scout discovery path.
DISCOVERY_DIRS = [PROJECT_ROOT / "src" / "discovery"]
DISCOVERY_EXTRA_FILES = [
    PROJECT_ROOT / "src" / "services" / "discovery_service.py",
    PROJECT_ROOT / "src" / "services" / "scout_report_service.py",
]


def _imported_modules_from_source(source: str) -> set[str]:
    """Return the set of module names imported by a Python source string."""
    tree = ast.parse(source)
    mods: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                mods.add(alias.name)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                mods.add(node.module)
    return mods


def _banned_hits(mods: set[str]) -> set[str]:
    """Modules that are, or descend from, a banned paid-AI SDK."""
    return {
        m for m in mods
        if any(m == b or m.startswith(b + ".") for b in BANNED_MODULES)
    }


def _discovery_files() -> list[Path]:
    files = [f for f in DISCOVERY_EXTRA_FILES if f.exists()]
    for base in DISCOVERY_DIRS:
        files.extend(p for p in base.rglob("*.py") if "__pycache__" not in p.parts)
    return files


def test_guard_has_teeth_detects_a_banned_import():
    """If a paid-AI import ever appears, the detector must catch it."""
    synthetic = "import openai\nfrom anthropic import Anthropic\nimport json\n"
    hits = _banned_hits(_imported_modules_from_source(synthetic))
    assert hits == {"openai", "anthropic"}


def test_discovery_path_imports_no_paid_ai_sdk():
    offenders: dict[str, set[str]] = {}
    for pyfile in _discovery_files():
        hits = _banned_hits(_imported_modules_from_source(pyfile.read_text(encoding="utf-8")))
        if hits:
            offenders[str(pyfile.relative_to(PROJECT_ROOT))] = hits
    assert not offenders, f"Paid-AI SDK imported in discovery path: {offenders}"


def test_candid_api_source_disabled_by_default():
    assert CandidApiSource().enabled is False
```

- [ ] **Step 2: Run the guard-has-teeth test to prove RED→GREEN mechanics**

Run: `conda run -n gmas python -m pytest tests/unit/test_no_paid_ai.py::test_guard_has_teeth_detects_a_banned_import -v`
Expected: PASS — proves the detector flags `openai`/`anthropic`. (This is the teeth check that stands in for a red step, since the real invariant already holds.)

- [ ] **Step 3: No production change needed**

T1 is a pure guard. Do not modify any `src/` file. If Step 4 fails, that is a *real* NFR-SCOUT-002 violation — stop and report; do not weaken the test.

- [ ] **Step 4: Run the full T1 file to verify the invariant holds**

Run: `conda run -n gmas python -m pytest tests/unit/test_no_paid_ai.py -q`
Expected: `3 passed`.

- [ ] **Step 5: Gate — full suite**

Run: `conda run -n gmas python -m pytest -q`
Expected: `177 passed` (174 baseline + 3 new).

- [ ] **Step 6: Commit**

```bash
git add tests/unit/test_no_paid_ai.py
git commit -m "test(scout): guard no-paid-AI + Candid-off-by-default (closes G1/NFR-SCOUT-002)"
```

---

### Task 2: Unit-test the strong-match green surfacing (G2 / FR-SCOUT-304)

**Files:**
- Create: `src/discovery/queue_label.py`
- Modify: `src/app/pages/09_discover.py` (remove inline `_queue_label` def at lines 30–35; import the helper instead)
- Create: `tests/unit/test_scout_queue_label.py`

**Interfaces:**
- Produces: `queue_label(candidate) -> str` in `src/discovery/queue_label.py`. Reads `candidate.is_strong_match`, `candidate.eligibility_status` (compared to `EligibilityStatus.ELIGIBLE`), `candidate.fit_score`, `candidate.act_now`, `candidate.raw_title`, `candidate.source`.
- Consumes: `src.models.discovered_candidate.EligibilityStatus`.

**Why this shape:** the label logic is currently trapped inside the Streamlit page (`09_discover.py:30`), so it can only be smoke-tested. Extracting a pure function makes FR-SCOUT-304's green/⏰ surfacing directly assertable with `SimpleNamespace` fakes — no Streamlit runtime.

- [ ] **Step 1: Write the failing test**

Create `tests/unit/test_scout_queue_label.py`:

```python
# ============================================================
# File: tests/unit/test_scout_queue_label.py
# Description: FR-SCOUT-304 — the ranked-queue label must surface a strong
#   eligible match as green (🟢), an eligible-but-not-strong as 🟡, everything
#   else as ⚪, an Act-Now candidate with ⏰, and a missing fit as "—".
# ============================================================

from __future__ import annotations

from types import SimpleNamespace

from src.discovery.queue_label import queue_label
from src.models.discovered_candidate import EligibilityStatus


def _cand(**overrides):
    base = dict(
        is_strong_match=False,
        eligibility_status=EligibilityStatus.UNKNOWN,
        fit_score=5.0,
        act_now=False,
        raw_title="Youth STEM Opportunity Fund",
        source="grants.gov",
    )
    base.update(overrides)
    return SimpleNamespace(**base)


def test_strong_eligible_is_green_with_fit():
    label = queue_label(_cand(
        is_strong_match=True,
        eligibility_status=EligibilityStatus.ELIGIBLE,
        fit_score=8.5,
    ))
    assert label.startswith("🟢")
    assert "fit 8.5" in label


def test_eligible_not_strong_is_yellow():
    label = queue_label(_cand(
        is_strong_match=False,
        eligibility_status=EligibilityStatus.ELIGIBLE,
    ))
    assert label.startswith("🟡")
    assert "🟢" not in label


def test_ineligible_is_neither_green_nor_yellow():
    label = queue_label(_cand(
        is_strong_match=False,
        eligibility_status=EligibilityStatus.INELIGIBLE,
    ))
    assert label.startswith("⚪")
    assert "🟢" not in label


def test_act_now_shows_clock():
    label = queue_label(_cand(
        is_strong_match=True,
        eligibility_status=EligibilityStatus.ELIGIBLE,
        fit_score=9.0,
        act_now=True,
    ))
    assert "⏰" in label


def test_missing_fit_renders_dash():
    label = queue_label(_cand(fit_score=None))
    assert "fit —" in label


def test_title_truncated_to_52_chars():
    long_title = "X" * 100
    label = queue_label(_cand(raw_title=long_title))
    assert "X" * 52 in label
    assert "X" * 53 not in label
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `conda run -n gmas python -m pytest tests/unit/test_scout_queue_label.py -q`
Expected: FAIL — `ModuleNotFoundError: No module named 'src.discovery.queue_label'`.

- [ ] **Step 3: Create the pure helper**

Create `src/discovery/queue_label.py`:

```python
# ============================================================
# File: src/discovery/queue_label.py
# Version: 1.0.0
# Description: Pure, UI-free helper that renders a discovered candidate's
#   one-line ranked-queue label. Extracted from the Streamlit Scout page so the
#   green / 🟡 / ⚪ / ⏰ surfacing logic (FR-SCOUT-304) is unit-testable.
# ============================================================

from __future__ import annotations

from src.models.discovered_candidate import EligibilityStatus


def queue_label(c) -> str:
    """One-line queue label: green flag for strong eligible matches, fit, urgency."""
    flag = "🟢" if c.is_strong_match else (
        "🟡" if c.eligibility_status == EligibilityStatus.ELIGIBLE else "⚪"
    )
    fit = f"{c.fit_score:.1f}" if c.fit_score is not None else "—"
    act = " ⏰" if c.act_now else ""
    return f"{flag}{act}  {c.raw_title[:52]}  ·  fit {fit}  ·  {c.source}"
```

- [ ] **Step 4: Point the Streamlit page at the helper**

In `src/app/pages/09_discover.py`, add the import next to the other `src.discovery`/`src.services` imports (near line 19):

```python
from src.discovery.queue_label import queue_label as _queue_label
```

Then delete the inline definition (current lines 30–35):

```python
def _queue_label(c) -> str:
    """One-line queue label: green flag for strong eligible matches, fit, urgency."""
    flag = "🟢" if c.is_strong_match else ("🟡" if c.eligibility_status == EligibilityStatus.ELIGIBLE else "⚪")
    fit = f"{c.fit_score:.1f}" if c.fit_score is not None else "—"
    act = " ⏰" if c.act_now else ""
    return f"{flag}{act}  {c.raw_title[:52]}  ·  fit {fit}  ·  {c.source}"
```

The call site at line 245 (`labels = {_queue_label(c): c.id for c in candidates}`) is unchanged because the import is aliased to `_queue_label`. Leave the `EligibilityStatus` import in the page — it is still used at lines 237 and 252.

- [ ] **Step 5: Run the test to verify it passes**

Run: `conda run -n gmas python -m pytest tests/unit/test_scout_queue_label.py -q`
Expected: `6 passed`.

- [ ] **Step 6: Verify the page still imports cleanly (no Streamlit runtime)**

Run: `conda run -n gmas python -c "import ast, pathlib; ast.parse(pathlib.Path('src/app/pages/09_discover.py').read_text(encoding='utf-8')); print('page parses OK')"`
Expected: `page parses OK` (guards against a botched edit; a full import would execute Streamlit `main()`).

- [ ] **Step 7: Gate — full suite**

Run: `conda run -n gmas python -m pytest -q`
Expected: `183 passed` (177 after T1 + 6 new).

- [ ] **Step 8: Commit**

```bash
git add src/discovery/queue_label.py src/app/pages/09_discover.py tests/unit/test_scout_queue_label.py
git commit -m "refactor(scout): extract testable queue_label helper + unit tests (closes G2/FR-SCOUT-304)"
```

---

### Task 3: Guard the seed criteria (G3)

**Files:**
- Create: `tests/integration/test_seed_scoring.py`
- Modify (only if the test proves a real defect): `src/db/seed_data.py` `DEFAULT_CRITERIA`

**Interfaces:**
- Consumes: `src.db.seed_data.DEFAULT_CRITERIA` (the exact list the seeder stores as `SelectionCriteria.criteria_json`); `src.discovery.evaluator.evaluate_candidate(extracted, criteria_list, org)`; `src.models.discovered_candidate.EligibilityStatus`.
- Produces: nothing consumed later. Guard.

**Why this shape:** G3 is a *production* risk — unit tests use synthetic criteria, so a seed whose `config` keys don't match the engine would score every real candidate 0.0 while the suite stays green. This test runs the **seeded constant**, JSON-round-tripped exactly as the DB stores it (`json.loads(json.dumps(DEFAULT_CRITERIA))`), through the real engine. Reading the code confirms the seed already uses the correct keys, so this test is expected to pass on the first run — it locks that in. The org fake mirrors the real profile (`has_501c3: false`, `default_fiscal_sponsor: "Teen Empowerment"`).

- [ ] **Step 1: Write the failing test**

Create `tests/integration/test_seed_scoring.py`:

```python
# ============================================================
# File: tests/integration/test_seed_scoring.py
# Description: G3 guard — the SEEDED active SelectionCriteria (DEFAULT_CRITERIA)
#   must be in the ScoringEngine's `config` schema. Round-trips the seed through
#   JSON exactly as the DB stores it, runs it through the real evaluator, and
#   asserts a matching grant scores > 0 and a hard-filtered one is INELIGIBLE.
#   Protects FR-SCOUT-301 / 304 in production (synthetic-criteria unit tests
#   cannot catch a bad seed).
# ============================================================

from __future__ import annotations

import json

from src.db.seed_data import DEFAULT_CRITERIA
from src.discovery.evaluator import evaluate_candidate
from src.models.discovered_candidate import EligibilityStatus

# The org as seeded from the real profile: no own 501(c)(3), but a default
# fiscal sponsor is available (so fiscal-sponsored grants are ELIGIBLE).
_ORG = type("Org", (), {
    "eligibility_json": json.dumps({
        "has_501c3": False,
        "default_fiscal_sponsor": "Teen Empowerment",
    })
})()


def _seeded_criteria() -> list[dict]:
    """Exactly what discovery_service reads back: json.loads(criteria_json)."""
    return json.loads(json.dumps(DEFAULT_CRITERIA))


def test_seed_scores_a_matching_grant_above_zero():
    matching = {
        "title": "Somerville Youth STEM After-School Fund",
        "target_geography": "Massachusetts",
        "focus_areas": ["Youth Development", "STEM", "After School"],
        "eligibility_501c3_required": True,   # allowed via fiscal sponsor
        "fiscal_sponsorship_allowed": True,
        "amount_min": 25000,
        "amount_max": 100000,
        "deadline": "2026-12-01",
    }
    ev = evaluate_candidate(matching, _seeded_criteria(), _ORG)
    assert ev.fit_score > 0.0
    assert ev.eligibility_status == EligibilityStatus.ELIGIBLE


def test_seed_marks_a_hard_filtered_grant_ineligible():
    ineligible = {
        "title": "Members-only 501(c)(3) Endowment",
        "target_geography": "Massachusetts",
        "focus_areas": ["Youth Development"],
        "eligibility_501c3_required": True,
        "fiscal_sponsorship_allowed": False,   # hard filter — org has no own 501c3
        "amount_min": 25000,
        "amount_max": 100000,
        "deadline": "2026-12-01",
    }
    ev = evaluate_candidate(ineligible, _seeded_criteria(), _ORG)
    assert ev.eligibility_status == EligibilityStatus.INELIGIBLE


def test_guard_has_teeth_a_misconfigured_seed_would_score_zero_on_focus():
    """If the seed used the wrong focus config key, focus_area credit vanishes."""
    broken = _seeded_criteria()
    for rule in broken:
        if rule.get("type") == "focus_area":
            # Simulate the classic seed bug: wrong config key.
            rule["config"] = {"focus_areas": rule["config"]["target_focus_areas"]}
    matching = {
        "title": "Somerville Youth STEM After-School Fund",
        "target_geography": "Nowhere",           # no geo credit either
        "focus_areas": ["Youth Development", "STEM"],
        "eligibility_501c3_required": False,
        "fiscal_sponsorship_allowed": True,
        "amount_min": 25000,
        "amount_max": 100000,
        "deadline": "2026-12-01",
    }
    good = evaluate_candidate(matching, _seeded_criteria(), _ORG).fit_score
    bad = evaluate_candidate(matching, broken, _ORG).fit_score
    assert bad < good  # proves the guard is sensitive to the config schema
```

- [ ] **Step 2: Run the test**

Run: `conda run -n gmas python -m pytest tests/integration/test_seed_scoring.py -q`
Expected: `3 passed` — the seed is already in the correct `config` schema (confirmed by reading `src/db/seed_data.py` and `src/engine/scoring_engine.py`).

- [ ] **Step 3: If (and only if) the seed guard failed — fix the seed**

If `test_seed_scores_a_matching_grant_above_zero` fails with fit `0.0`, the seed's `config`
keys are wrong. Rewrite each `DEFAULT_CRITERIA` entry's `config` to the schema in Global
Constraints (`target_geographies`, `target_focus_areas`, `min_acceptable`,
`max_acceptable`), keeping `type` / `weight` / `is_hard_filter`. Re-run Step 2 until green.
**Log the fix** in `00_Project_Planning/DISAMBIGUATION_RECORD_v1.0.md` as the next `D-0xx`.
(Expected: not needed — reading the code shows the seed is already correct.)

- [ ] **Step 4: Gate — full suite**

Run: `conda run -n gmas python -m pytest -q`
Expected: `186 passed` (183 after T2 + 3 new).

- [ ] **Step 5: Commit**

```bash
git add tests/integration/test_seed_scoring.py
git commit -m "test(scout): guard seeded criteria score real grants (closes G3)"
```

(If Step 3 changed `seed_data.py`, add it to this commit and append `+ fix seed config schema (D-0xx)` to the message.)

---

### Task 4: Certify the branch (Phase 4 — code review)

**Files:** none created. Review-and-triage only; any fix re-enters the TDD loop above.

- [ ] **Step 1: Confirm the RTM is fully closed**

Update `00_Project_Planning/Scout-Agent-Task-Plan-v1.1.0.md` §3: flip NFR-SCOUT-002 and
FR-SCOUT-304 to ✅ (referencing `test_no_paid_ai`, `test_scout_queue_label`,
`test_seed_scoring`). Confirm zero ❌ and zero 🟡.

- [ ] **Step 2: Verify the whole suite is green**

Run: `conda run -n gmas python -m pytest -q`
Expected: `186 passed` (or higher). Orchestrator reads the output — no claim without it.

- [ ] **Step 3: Request the review**

Invoke `superpowers:requesting-code-review` (or `/code-review` at high effort) over the diff
`main..feat/grantnova-scout`. Focus areas (from spec §6): eligibility/ranking edge cases,
date/amount parsing, report read-only guarantee, migration reversibility, scoring-engine
reuse (no duplicated math), robots/rate-limit not bypassable, ToS blocklist intact, no
secrets, meaningful assertions, no real-DB/network in tests.

- [ ] **Step 4: Triage findings**

For each finding, mark fix-now / follow-up / won't-fix. Vet suggestions with
`superpowers:receiving-code-review` before acting. Every fix-now goes through the §5 TDD
loop (failing test → minimal fix → green → full-suite gate → commit). Log any judgment call
to the Disambiguation Record.

- [ ] **Step 5: Final gate + handoff**

Run: `conda run -n gmas python -m pytest -q`
Expected: green. Then the branch is ready for the owner's merge/PR decision
(`superpowers:finishing-a-development-branch`). Do not merge or push without the owner.

---

## Self-Review (author checklist — completed)

- **Spec coverage:** G1→Task 1, G2→Task 2, G3→Task 3, §6 review→Task 4. All three RTM gaps and the certify phase are covered.
- **Placeholder scan:** no TBD/"add error handling"/"write tests for the above" — every code step contains complete, runnable content.
- **Type consistency:** `queue_label` (defined Task 2) is imported with the same name/signature; `evaluate_candidate(extracted, criteria_list, org)` matches `src/discovery/evaluator.py`; `EligibilityStatus.{ELIGIBLE,INELIGIBLE,UNKNOWN}` and `CandidApiSource.enabled` match the read source; config keys match `scoring_engine.py`.
- **Test counts** (174 → 177 → 183 → 186) assume the stated baseline; if the baseline differs, adjust the expected totals but keep the per-task deltas (+3, +6, +3).
