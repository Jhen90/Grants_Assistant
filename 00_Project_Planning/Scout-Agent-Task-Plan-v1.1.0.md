---
title: GrantNova Grant Scout — Agent Task Plan (Certify · TDD-close gaps · Review)
version: 1.1.0
supersedes: Scout-Agent-Task-Plan-v1.0.0.md
created: 2026-07-23
status: DRAFT — awaiting owner confirmation before execution
methodology: Superpowers (writing-plans → subagent-driven-development → test-driven-development → requesting-code-review)
change-note: >
  v1.1.0 updates the "skills availability" caveat only. The Superpowers skills are now
  INSTALLED and INVOKABLE by name in this environment (the `Skill` tool resolves
  superpowers:writing-plans, subagent-driven-development, test-driven-development,
  requesting-code-review, verification-before-completion, executing-plans, etc.). The
  audit, gap list (G1–G3), and task decomposition (T1–T3) are unchanged.
---

# Grant Scout — Agent Task Plan v1.1.0

## 0. What this plan is (and how it differs from the rough prompt)

The rough prompt (v0.5.0) asked, in order, to: (1) review the Scout PRD, (2) ensure every
requirement has an acceptance criterion, (3–4) produce an agent task plan using the
**subagent-driven-development** skill, (5) execute it using **test-driven-development**,
and (6) finish with the **requesting-code-review** skill.

This turns that into a structured plan **grounded in current reality**: the Grant Scout
module is already **built and green** (7 commits on `feat/grantnova-scout`, full suite
**174 passing**, DB at Alembic head 004). So this is not a greenfield build — it is a
**certify → close-gaps (TDD) → review** plan. It:

1. **Audits** the PRD so every FR-SCOUT / NFR-SCOUT requirement is provably tied to an
   acceptance criterion and a runnable test (Requirements Traceability Matrix, §3).
2. **Decomposes** the *remaining* work into agent tasks under the subagent-driven-development
   pattern (§4).
3. **Executes** those tasks strictly test-first — red → green → refactor (§5).
4. **Certifies** the whole module with a final code-review pass (§6).

> **Skills availability (updated in v1.1.0):** the Superpowers skills are now **installed
> and invokable by name** here — the `Skill` tool resolves `superpowers:writing-plans`,
> `superpowers:subagent-driven-development`, `superpowers:test-driven-development`,
> `superpowers:requesting-code-review`, `superpowers:verification-before-completion`, and
> `superpowers:executing-plans`, among others. This changes the execution model from
> v1.0.0: the §4 tasks **can now be dispatched to real implementer subagents** under
> subagent-driven-development (fresh subagent per task + two-stage review), rather than the
> orchestrator simulating them inline. The orchestrator still owns the verification gate
> (§7): it re-runs every VERIFY command itself before any task is called "done"
> (verification-before-completion). Subagents remain sandboxed per the working agreement.

## 1. Current reality (the baseline this plan builds on)

- Branch `feat/grantnova-scout`, **7 commits**, not merged/pushed.
- Full suite **174 passing** in the `gmas` conda env; DB `grantnova.db` at Alembic **004**.
- Scout code: `src/discovery/` (sources, query_expander, fetcher, extractor, evaluator),
  `src/services/discovery_service.py`, `src/services/scout_report_service.py`,
  `src/app/pages/09_discover.py`, `scripts/run_discovery_scan.py`.
- Requirements: PRD v1.2.0 §2.13 (**24** requirements: 17 FR-SCOUT + 7 NFR-SCOUT);
  design in HLD v1.2.0 §14; build plan + acceptance criteria in
  `05_Grant_Scout_Task_Implementation_Plan_v1.0.0.md`; decisions D-016–D-024.

## 2. Skill → phase mapping (the methodology the rough prompt requested)

| Phase | Superpowers skill (now invokable by name) | Output |
|---|---|---|
| 1. Audit | `superpowers:writing-plans` + the plan's own AC discipline | Requirements Traceability Matrix; gap list |
| 2. Decompose | `superpowers:subagent-driven-development` | Discrete agent tasks with roles, inputs, AC, VERIFY |
| 3. Execute | `superpowers:test-driven-development` | Failing test first → minimal code → green → refactor |
| 4. Certify | `superpowers:requesting-code-review` | Reviewed diff `main..feat/grantnova-scout`; findings triaged |
| (gate) | `superpowers:verification-before-completion` | Orchestrator re-runs every VERIFY before "done" |

---

## 3. Phase 1 — PRD review + Requirements Traceability Matrix (RTM)

**Goal (rough-prompt items 1–2):** every Scout requirement is provably covered by an
acceptance criterion and an automated test. Below is the audit. **Legend:** ✅ covered by a
passing automated test · 🟡 covered only by manual/smoke check · ❌ no automated coverage.

| Requirement | Acceptance criterion (what proves it) | Test / evidence | Status |
|---|---|---|---|
| FR-SCOUT-101 sources | connectors map results to candidates | `test_grants_gov_source`, `test_web_search_source`, `test_funder_site_source` | ✅ |
| FR-SCOUT-102 ≤40 query expansion | dedupe + cap | `test_query_expander` | ✅ |
| FR-SCOUT-103 disabled-safe | disabled source → `[]` | `*_source` disabled tests | ✅ |
| FR-SCOUT-201 robots/rate/cache/UA | robots-deny→None; cache skips net; rate-limit sleeps | `test_fetcher` | ✅ |
| FR-SCOUT-202 deterministic extract | same input → same output | `test_extractor::determinism` | ✅ |
| FR-SCOUT-203 confidence + evidence | each field carries both | `test_extractor` | ✅ |
| FR-SCOUT-204 ToS domains blocked | blocked hosts dropped | `test_web_search_source` | ✅ |
| FR-SCOUT-301 fit at stage-time | staged candidate has fit_score | `test_discovery_service`, `test_scout_pipeline` | ✅ |
| FR-SCOUT-302 eligibility + fiscal sponsor | hard-filter→INELIGIBLE; sponsor→ELIGIBLE; none→UNKNOWN | `test_candidate_evaluator` | ✅ |
| FR-SCOUT-303 ranked queue | strong/eligible/fit ordering | `test_scout_pipeline` | ✅ |
| FR-SCOUT-304 strong = green | `is_strong_match` set; surfaced green | evaluator unit ✅ / UI label 🟡 | 🟡 |
| FR-SCOUT-305 idempotent re-eval | stable scores, no dup rows | `test_scout_pipeline` | ✅ |
| FR-SCOUT-306 urgency + Act Now | urgency classified; act_now flag | `test_candidate_evaluator` | ✅ |
| FR-SCOUT-401 digest, Act-Now first | renders; ordering | `test_scout_report` | ✅ |
| FR-SCOUT-402 Jinja, UI + CLI | CLI `--report` exit 0; render | `test_scout_report` + CLI smoke | ✅ |
| FR-SCOUT-403 fields + unverified | low-confidence marked unverified | `test_scout_report` | ✅ |
| FR-SCOUT-404 read-only | statuses unchanged | `test_scout_report` | ✅ |
| NFR-SCOUT-001 determinism | evaluator deterministic | `test_candidate_evaluator::deterministic` | ✅ |
| NFR-SCOUT-002 no paid AI | no paid-AI client in the path; Candid off by default | *(inspection only)* | ❌ |
| NFR-SCOUT-003 human-in-the-loop | evaluate creates 0 grants | `test_scout_pipeline` | ✅ |
| NFR-SCOUT-004 politeness | rate-limit + cache + robots | `test_fetcher` | ✅ |
| NFR-SCOUT-005 test coverage / no real DB | suite green; in-memory DBs | full suite + `conftest` | ✅ |
| NFR-SCOUT-006 Alembic authoritative + drift guard | ORM↔migration parity | `test_migrations` | ✅ |
| NFR-SCOUT-007 reversible migrations | downgrade→upgrade round-trip | `test_migrations` | ✅ |

**Audit result — 3 gaps to close (the entire scope of Phase 3):**

- **G1 (❌ NFR-SCOUT-002):** "no paid AI" has no automated guard. A regression could add a
  paid client unnoticed.
- **G2 (🟡 FR-SCOUT-304):** the green/strong-match *surfacing* is only smoke-tested at the
  page level; the queue-label logic has no unit test.
- **G3 (correctness risk, from the handoff):** the **seeded** active `SelectionCriteria`
  must be in the scoring engine's `config` format — if not, every candidate scores 0.0 and
  FR-SCOUT-301/304 are effectively dead in production even though unit tests pass on
  synthetic criteria. No test guards the *seed*.

**Phase 1 deliverable:** this RTM committed into the plan; G1–G3 confirmed as the only gaps.

---

## 4. Phase 2 — Agent-task decomposition (subagent-driven-development)

Three self-contained tasks, each written so it can be handed to an implementer subagent
(role, inputs, constraints, acceptance criteria, VERIFY). With skills now invokable, these
tasks **are** dispatchable to fresh implementer subagents under
`superpowers:subagent-driven-development`; the orchestrator reviews between tasks and owns
the verification gate.

### Task T1 — Guard "no paid AI" (closes G1 / NFR-SCOUT-002)
- **Role:** implementer (TDD).
- **Files:** `tests/unit/test_no_paid_ai.py` (new). No production change expected.
- **Spec:** assert the discovery path imports no paid-AI SDK, and that `CandidApiSource`
  is disabled by default (`candid_api_enabled=False`, empty key → `enabled is False`).
- **AC / VERIFY:** `pytest tests/unit/test_no_paid_ai.py -q` → passes; test fails if a paid
  client import is added or Candid defaults to on.

### Task T2 — Unit-test the strong-match green surfacing (closes G2 / FR-SCOUT-304)
- **Role:** implementer (TDD).
- **Files:** `tests/unit/test_scout_queue_label.py` (new); extract the label logic from the
  Streamlit page into a pure helper `queue_label(candidate)` in a testable module so it can
  be asserted without a UI runtime.
- **AC / VERIFY:** `pytest tests/unit/test_scout_queue_label.py -q` → a strong eligible
  candidate yields the 🟢 label + fit; an ineligible one does not; an Act-Now one shows ⏰.

### Task T3 — Guard the seed criteria (closes G3)
- **Role:** implementer (TDD) — may surface a real seed bug.
- **Files:** `tests/integration/test_seed_scoring.py` (new); **if** the test fails, fix the
  seeded criteria in `src/db/seed_data.py` to the engine's `config` schema
  (`target_geographies` / `target_focus_areas` / `min_acceptable` / `max_acceptable` /
  `is_hard_filter`). Any fix logged as a D-0xx decision.
- **AC / VERIFY:** `pytest tests/integration/test_seed_scoring.py -q` → the seeded active
  `SelectionCriteria` scores a known-matching sample grant **> 0.0** and marks a clearly
  ineligible one INELIGIBLE.

**Dependencies:** T1, T2, T3 are independent and may run in any order (dispatchable in
parallel to subagents). All are additive (new test files; T2 touches one production file).

---

## 5. Phase 3 — Execute, test-first (test-driven-development)

For **each** of T1–T3, follow the strict loop — no production code before a failing test:

1. **RED** — write the test expressing the requirement; run it; **confirm it fails** for the
   right reason (paste the failure). For guard tests where the invariant already holds
   (T1/T3), the red/green proof is a "guard-has-teeth" sub-test that deliberately feeds a
   violating input and asserts the guard catches it.
2. **GREEN** — write the minimum code to pass (T1 none; T2 a small helper extraction;
   T3 the seed fix only if RED proves a real defect).
3. **REFACTOR** — clean up with tests staying green.
4. **GATE** — run the **full suite**; must be ≥ 174 passing. Orchestrator re-runs it.
5. **COMMIT** — one commit per task (per-WP cadence), message noting the requirement closed.

**Exit criterion for Phase 3:** RTM has **zero ❌ and zero 🟡**; full suite green; any seed
fix committed and logged.

---

## 6. Phase 4 — Final quality review (requesting-code-review)

Once Phase 3 is green, invoke `superpowers:requesting-code-review` over the **entire Scout
diff** `main..feat/grantnova-scout` (or the local `/code-review` skill at high effort). The
review targets **quality, not new features**:

- **Correctness:** eligibility/ranking edge cases; date/amount parsing; report read-only
  guarantee; migration reversibility.
- **Reuse/simplicity:** evaluator's reuse of the scoring engine; no duplicated scoring math;
  dead code; over-broad `except`.
- **Security/politeness:** robots/rate-limit not bypassable; ToS-domain blocklist intact;
  no secrets; SQL built safely.
- **Tests:** assertions are meaningful (not hollow); no test touches the real DB; network
  fully mocked.

**Handling findings:** triage each as fix-now / follow-up / won't-fix; fixes go through the
same TDD loop (§5) and re-verify; decisions logged. Apply `superpowers:receiving-code-review`
to vet each suggestion rather than accept blindly.

**Phase 4 deliverable:** a reviewed, green branch with findings triaged — ready for the
merge/PR decision (owner's call; see `05_...TIP` and the handoff).

---

## 7. Orchestration guardrails (standing working agreement)

- **Verify by command, never by claim.** Every task's "done" = orchestrator re-runs its
  VERIFY and reads the output (verification-before-completion).
- **Commit per task** for incremental reversibility.
- **Log autonomous decisions** to `DISAMBIGUATION_RECORD_v1.0.md` (D-025+).
- **Background/implementer subagents** stay in a strict per-project sandbox; the
  orchestrator reviews between tasks and owns the final gate.

## 8. Definition of Done

1. RTM shows every FR-SCOUT/NFR-SCOUT requirement ✅ (automated test), no ❌/🟡.
2. Full suite green (target ≥ 177 after T1–T3).
3. Seed scoring verified against real seeded criteria (G3 closed).
4. Code-review complete; findings triaged and fixes verified.
5. Branch ready for the owner's merge/PR decision.

## 9. Open decisions (need owner confirmation before execution)

1. **Proceed now?** Execute Phase 1–4 under the established per-task-commit cadence.
2. **Execution model:** now that skills are invokable, dispatch T1–T3 to fresh implementer
   subagents (`superpowers:subagent-driven-development`) with orchestrator review between
   tasks, **or** run them inline (`superpowers:executing-plans`)? Recommend
   subagent-driven for T1–T3 (independent, additive), orchestrator-verified.
3. **Review engine for Phase 4:** `superpowers:requesting-code-review` (now available) vs.
   the local `/code-review` skill. Recommend `/code-review` at high effort now for a
   fast pass; both can run.
4. **T2 refactor:** OK to extract the queue-label helper out of the Streamlit page into a
   testable module (`src/discovery/queue_label.py`)? (Recommended — enables a real unit test.)
