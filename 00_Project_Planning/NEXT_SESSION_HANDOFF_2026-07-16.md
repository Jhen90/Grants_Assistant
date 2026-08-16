---
title: GrantNova — Next-Session Handoff
date: 2026-07-16
branch: feat/grantnova-scout
next_session: 2026-07-17 (morning)
---

# Pick-up instructions for the next session (start here)

## 0. Where we are (verified 2026-07-16, end of session)

- **Branch:** `feat/grantnova-scout` — **8 commits ahead of `main`, not merged, not pushed.**
- **Tests:** full suite **174 passing** in the `gmas` conda env.
- **Database:** `data/grantnova.db`, Alembic head **004**. Seeded with 32 funders,
  14 templates, 1 org, 1 selection-criteria set. **0 grants, 0 discovered candidates**
  (the Scout queue is empty until you run a search — see Step 2).
- The Scout module (Hunt → Gather → Evaluate → Report) is fully built, tested, and
  documented. Full plan + acceptance criteria: `05_Grant_Scout_Task_Implementation_Plan_v1.0.0.md`.
- Backup of the pre-rename DB: `data/backups/gmas.db.pre-grantnova-20260716.bak`.

## 1. Resume & sanity-check the environment (2 min)

```bash
conda activate gmas
cd C:\Users\jhenn\OneDrive\Desktop\01_Projects\Grants_Assistant
git branch --show-current          # expect: feat/grantnova-scout
python -m pytest -q                 # expect: 174 passed
python -m alembic current           # expect: 004 (head)
```
If any of those don't match, stop and investigate before testing.

1
## 2. FIRST TASK — run the Scout module and test it

### 2a. Launch the app
```bash
start_grantnova.bat
# or:  streamlit run src/app/main.py
```
Open http://localhost:8501 → sidebar → **🛰️ Grant Scout** page (file `09_discover`).

### 2b. Populate the queue (needs internet)
On the **🔍 Search** tab:
- Try a targeted search first, e.g. `youth development STEM grant Massachusetts 2026`,
  sources = grants.gov + Web search → **Search this query**.
- Then try **🌐 Search Everywhere** (full sweep — takes a few minutes; polite rate-limiting).

### 2c. Things to actually look at / test (capture feedback on each)
- **📋 Review Queue** — is it **ranked best-first**? Do strong eligible matches show the
  🟢 flag and ⏰ "act now" for near deadlines? Does **Hide ineligible** work? Does the
  strong-match banner + "why it fits" read sensibly?
- **Fit scores** — do they look reasonable? ⚠️ If *everything* scores 0.0, the seeded
  active `SelectionCriteria.criteria_json` may not be in the scoring engine's `config`
  format (target_geographies / target_focus_areas / min_acceptable / is_hard_filter).
  That's the most likely first-run surprise — flag it and we'll adjust the seed.
- **📊 Report** tab — **Generate digest**: is the layout useful? Act Now section first?
  Are low-confidence deadlines/amounts marked "(unverified)"? Download works?
- **Import flow** — pick a candidate, confirm the pre-filled form, **Import as Grant**;
  verify it appears in the Grants page with a score + status.
- **🔗 Scrape URL** — paste a real funder RFP page; check extraction + confidence flags.

### 2d. CLI path (optional)
```bash
python -m scripts.run_discovery_scan --report                 # fixed saved queries + digest
python -m scripts.run_discovery_scan --sweep --report         # full sweep + digest
```

### 2e. Capture feedback
Jot notes on: ranking quality, eligibility correctness (esp. fiscal-sponsorship cases),
extraction accuracy, report usefulness, and any errors. Bring that back to the session —
it drives the next round of tuning.

## 3. Outstanding / deferred (decide when ready)

- **Merge/PR**: `feat/grantnova-scout` → `main` (I did not push or merge — your call).
- **Deferred docs (D-024)**: bump Detailed Design + Overview to v1.2.0 (Scout detail
  currently lives authoritatively in the TIP).
- **Pre-existing untracked files** in the working tree (`.claude/`, AI transcripts,
  `GMAS-Alternative-Names*`, kickoff/notes scratch, two root-level deletions) — from
  before this work; decide whether to commit, move, or delete.
- **Transcript archive** `AI_Session_Transcripts/2026.07.16-…-c46dbd7d.jsonl` is a live
  snapshot (missing the very end of the session); re-copy if you want it complete.

## 4. Key references
- Plan + acceptance criteria: `00_Project_Planning/05_Grant_Scout_Task_Implementation_Plan_v1.0.0.md`
- Requirements: `01_PRD_v1.2.0.md` (§2.13) · Architecture: `02_High_Level_Design_v1.2.0.md` (§14)
- Autonomous decisions: `DISAMBIGUATION_RECORD_v1.0.md` (D-020–D-024)
- Scout code: `src/discovery/` (evaluator, extractor, fetcher, sources), `src/services/discovery_service.py`,
  `src/services/scout_report_service.py`, `src/app/pages/09_discover.py`

## 5. Tip for resuming with Claude
Point the new session at this file and the TIP. Reminders that carry over: **verify every
task with a runnable command (never trust a claim)**, **commit per Work Package**, and
**log any autonomous judgment call to the Disambiguation Record**.
