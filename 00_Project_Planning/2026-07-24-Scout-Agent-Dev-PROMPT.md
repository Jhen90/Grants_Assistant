# Grant Scout — Subagent-Driven Execution Prompts (2026-07-24)

Paste **Prompt A** into a fresh Claude Code session opened at the repo root
(`c:\Users\jhenn\OneDrive\Desktop\01_Projects\Grants_Assistant`) on branch
`feat/grantnova-scout`. It drives the whole run via `superpowers:subagent-driven-development`
(dispatches + reviews each task internally). Prompts B and C steer as results land.

**Plan being executed:** `00_Project_Planning/06_Grant_Scout_Certify_Close_Gaps_Plan_v1.0.0.md`
**Source spec:** `00_Project_Planning/Scout-Agent-Task-Plan-v1.1.0.md`

---

## Prompt A — kickoff (paste first)

```
Execute the plan at 00_Project_Planning/06_Grant_Scout_Certify_Close_Gaps_Plan_v1.0.0.md
using superpowers:subagent-driven-development. Read that plan and its source spec
(Scout-Agent-Task-Plan-v1.1.0.md) in full before starting.

Rules for this run:
- We are on branch feat/grantnova-scout. First run the baseline gate:
  `conda run -n gmas python -m pytest -q` and confirm 174 passed before touching anything.
  If it is not green, STOP and tell me.
- Tasks 1–3 are independent and additive — dispatch a fresh implementer subagent per task,
  each doing strict TDD (failing/teeth test first → minimal code → green). After each task,
  YOU (orchestrator) re-run its VERIFY command and the full suite yourself and read the
  output — never trust a subagent's claim 
  (verification-before-completion). Expected suite
  totals: 177 → 183 → 186.
- One commit per task with the co-author trailer, exactly as the plan specifies. Do NOT
  merge or push — that's my call.
- Task 3 may reveal a real seed bug. Only change src/db/seed_data.py if the seed test
  actually fails; if you do, log it as the next D-0xx in
  00_Project_Planning/DISAMBIGUATION_RECORD_v1.0.md.
- Task 4 (code review) runs only after T1–T3 are green: use /code-review at high effort over
  main..feat/grantnova-scout, then triage findings with me before applying any fix.

Pause and report to me after EACH task (show the VERIFY output + full-suite count) and wait
for my go-ahead before starting the next one. Start with the baseline gate now.
```

> **Variant — unattended T1–T3:** to let it run all three back-to-back and review them
> together, replace the last line of Prompt A with:
> *"Run T1–T3 back-to-back, then report all three together before Task 4."*

---

## Prompt B — between tasks (approve and continue)

```
Approved. Proceed to the next task. Same rules: fresh subagent, TDD, then you re-run VERIFY
+ full suite and show me the output before committing.
```

---

## Prompt C — review stage (Task 4, after you've seen findings)

```
For the review findings: apply only the ones I mark fix-now, each through the TDD loop
(failing test → minimal fix → green → full-suite gate → commit). Mark the rest as follow-up
in the plan. When the branch is green and the RTM shows zero ❌/🟡, summarize what changed
and stop — do not merge or push. Give me the finishing-a-development-branch options.
```

---

## What to check in each task report

- **Every task:** the new test file, the VERIFY line (`N passed`), and the full-suite count
  matching the expected total (177 → 183 → 186).
- **T1 (no-paid-AI):** `tests/unit/test_no_paid_ai.py`, 3 passed. No `src/` change.
- **T2 (queue label):** new `src/discovery/queue_label.py`, the aliased import edit in
  `src/app/pages/09_discover.py`, `tests/unit/test_scout_queue_label.py` 6 passed.
- **T3 (seed guard):** `tests/integration/test_seed_scoring.py` 3 passed. Confirm it did
  **not** need to touch `src/db/seed_data.py` (expected — the seed is already correct). If it
  did, look for the new D-0xx entry in the Disambiguation Record.
- **T4 (review):** RTM in `Scout-Agent-Task-Plan-v1.1.0.md` §3 flipped NFR-SCOUT-002 and
  FR-SCOUT-304 to ✅; findings triaged; branch green; no merge/push.

## Reminders

- Nothing here depends on the prior chat session — all paths are on disk.
- The orchestrator will not merge or push; that stays your decision
  (`superpowers:finishing-a-development-branch`).
# The Dojo at Somernova — Authoritative Grant-Ready Profile

> **This file is the single source of truth for any grant-search or grant-writing bot working on The Dojo.**
> When facts conflict elsewhere, this file wins.

---

## ⚠️ DATA INTEGRITY RULES — READ FIRST, NEVER BREAK

1. **Never call 11,776 "youth served."** It is **11,776 attendance instances (visits/participation instances)** recorded January–July 2026 (28 weeks). Describe it as attendance, visits, or participation instances — never as unique young people.
2. **Use unique-youth figures only when the data specifically counts unique participants.** The known unique/served figures are:
   - **~300 unique youth** participants for the **Teen Time** program specifically.
   - **More than 2,000 youth annually** served by The Dojo historically.
   - **20–40 youth** on most days; capacity for **up to 80** at larger events.
3. **These metrics measure different things and must never be combined** as if they were the same statistic.
4. **Do not insert every partner into every grant.** Select the partners that fit the specific funder and opportunity.
5. Keep every claim traceable to this sheet. If a fact isn't here, don't invent it — flag it as needing confirmation.

---

## What The Dojo is

The Dojo at Somernova is a **youth-centered, multigenerational community space** at **15 Properzi Way, Somerville, Massachusetts 02143**. It was established during the COVID-19 pandemic in response to community demand for a place where young people could safely gather, learn, create, connect with peers, build relationships with supportive adults, and access opportunities outside of school.

It is **not simply an after-school program.** It functions as a **physical youth hub and community platform** where structured programming, semi-structured activities, drop-in recreation, mentorship, workforce exposure, arts, media, climate education, civic engagement, and community events coexist.

**Core operating philosophy: flexibility.** Youth can attend a workshop, go to an event, work on a project, meet mentors, play games, make art, repair bikes, use computers, perform, eat, socialize, or simply have a safe place to spend time.

---

## 2026 attendance and youth engagement

From **January–July 2026 (28 weeks)**, The Dojo recorded:

- **11,776 total attendance instances** *(attendance/visits — NOT unique youth)*
- Average participant age: **14**
- Highest-attendance month: **July** (**2,144**)
- April–July attendance: **7,709**

**Monthly attendance:** January 1,167 · February 1,603 · March 1,297 · April 1,913 · May 1,861 · June 1,791 · July 2,144

**Weekly attendance totals:** Week 1 2,290 · Week 2 3,077 · Week 3 3,325 · Week 4 3,084

**Separate unique/served figures (Teen Time & historical):** ~300 unique Teen Time youth; 20–40 youth most days; up to 80 at larger events; **2,000+ youth annually** historically; **100+ community events** over the past five years.

---

## Who The Dojo serves

**Teen Time @ The Dojo** serves **Somerville youth ages 14–19.** Target population includes: Somerville youth citywide, immigrant youth, youth living in poverty, youth experiencing housing insecurity, youth designated "at risk" by civic/legal/educational systems, and young people with limited access to traditional enrichment. The program stays **open to youth across Somerville** rather than restricting to one population.

---

## The physical space (a major program asset)

Charging stations · indoor youth art/gallery space · outdoor youth art/gallery space · outdoor graffiti wall · fenced outdoor Parkour course · on-site bike-repair programming · premium filtered water · video-game consoles · computer access · books · board games · card games · couches · tables and chairs · arts and crafts supplies · projector · projection screen · refrigerator · microwave · indoor/outdoor garden · bike racks.

The space is **ADA compliant**, **accessible by public transportation**, and **within walking distance of Somerville High School.**

**Grant significance:** The Dojo does **not** need funding to build a youth facility from scratch. The infrastructure already exists — funding *leverages* it.

---

## Teen Time @ The Dojo

A **free youth drop-in and enrichment program** built around both unstructured and optional structured/semi-structured activities. Purpose is broader than recreation: relationship building, skill development, mentorship, opportunity creation, belonging, positive youth development, leadership, community engagement, and safe, reliable youth space.

**Schedule**
- **Summer (July–August):** Fridays 2:00–7:00 PM. Primarily open, supervised, unstructured youth space (games, art, computers, charging, social space, Dojo resources).
- **School year (September–June):** Wednesdays 2:00–5:00 PM (scheduled around Somerville's early-release day; monthly Open Mic Wednesdays may run to 6:00 PM). Fridays 2:00–8:00 PM (drop-in from 2:00 including X-Block early release; optional programming ~3:00 PM).

---

## What youth can actually do here

Play video games and tournaments; board/card games; use computers; charge phones; hang out; make art, paint, draw, graffiti/street-art and murals; use maker materials; Parkour/recreation; repair bikes and learn bike-repair; write and perform poetry/spoken word; sing, dance, make music, perform at Open Mics, Hip-Hop events, DJing, beat-making; create media, shoot videos, storytelling, blogs/digital content; youth discussions and leadership; financial literacy; career readiness (resume, interview, public speaking, communication); explore college/post-secondary; mentorship; meet professionals, entrepreneurs, artists, nonprofit leaders, elected officials, city staff, innovators; learn about climate careers and clean technology; STEM/STEAM; civic engagement; environmental education; field trips; community celebrations; youth showcases; eat snacks and meals; wellness, journaling, yoga/breathwork; or simply have a safe place to be.

Grant application explicitly lists: creative arts, civic engagement, youth-led culturally relevant discussions, leadership development, Open Mics, workforce readiness, life skills, mentorship, post-secondary preparation, financial literacy, clean-technology education, STEM and STEAM.

---

## Partners

**Books of Hope** — Somerville-founded creative writing & publishing program (originally connected to youth in/around the Mystic Housing Development). Brings creative writing, poetry, spoken word, performance, publication, communication skills, youth leadership, teaching-artist development, community organizing, creative youth development. At The Dojo: monthly writing + Open Mic — **3rd Wednesday** each month, 2:00–4:00 PM creative-writing workshop, 4:00–6:00 PM Open Mic Talent Show (poetry, spoken word, comedy, live art, music, singing, dance, other talents; featured local/regional artists; food included).

**The Center for Teen Empowerment** — Founded 1992; in Somerville since 2004. Employs youth ages 14–19 in year-round youth-leadership positions. Builds leadership, voice, peer engagement, civic participation, policy influence, workshop facilitation, event organizing, dialogue. **Lead applicant and fiscal sponsor** for the Teen Time @ The Dojo City grant. Responsibilities: program oversight, Wednesday facilitation, youth outreach/engagement, community events, partnership coordination, data collection, reporting, fiscal sponsorship, invoicing the City, grant logistics.

**Teen Talk** — Recurring youth-led discussions run by Teen Empowerment Youth Organizers on issues that matter to youth: identity, culture, stress, peer support, community issues, organizing, social/emotional differences, current events, youth concerns/fears/hopes, decision-making, mental health, LGBTQ+ topics, substance misuse, and other sensitive issues. Professional partners brought in for specialized/trauma-informed support when appropriate.

**Somerville Bike Kitchen** — Operates within the Dojo ecosystem (The Dojo provides space). Community repair nights, bicycle repair, repair classes, community bike events, youth education, event participation. Pathway into mechanical skills, transportation/mobility, sustainability, STEM, skilled trades, community service, climate learning.

**Better Future Project** — Dojo/Somernova partner (The Dojo provides space at a significantly reduced rate). Climate organizing and education for Somerville residents. Opportunities: climate education, environmental justice, youth organizing, sustainability, civic participation, clean energy, climate leadership.

**Somerville Media Center** — Active partner. Youth work: video, youth media, storytelling, blogging, digital production, interviews, community journalism, media literacy, creative production.

**Greentown Labs** — Community partner. Field trips, climate-tech exposure, STEM, career exploration, meetings with innovators, climate workforce awareness, entrepreneurship, clean-energy education.

**Other documented partners** (select per opportunity, don't dump all): Better Future Project · Cambridge Health Alliance · Creative by Nature · Greentown Labs · Harvard Graduate School of Education · Mystic Learning Center · Somerville Bike Kitchen · Somerville Department of Racial and Social Justice · Somerville Health and Human Services · Somerville Youth Services · Somerville Prevention Services · Somerville Media Center · Somerville Mentorship Team · Somerville Neighborhood Counseling Services · Somerville Office of Immigrant Affairs · Parkour organizations/programming.

---

## Career readiness & life skills

College essay writing · post-secondary prep · resume writing · interviewing · financial literacy · Know Your Rights workshops · communication skills · difficult-conversation skills · youth leadership · public speaking · nutrition · cooking · environmental preservation.

**Friday Teen Time** combines recreation with education and mentorship; youth receive snacks and drinks (food intentionally reduces barriers and builds relationships). Activities: indoor sports, team-building, board-game and video-game tournaments, art/painting/maker projects, field-trip and event prep, Hip-Hop Culture Nights, music, dance, spoken word, DJing, beat-making, live performance.

**Career/professional exposure:** guest speakers, mentors, entrepreneurs, business leaders, elected officials, artists, innovators, Somernova professionals, nonprofits, city departments, educational institutions, community organizations. Subjects: career exploration, workforce readiness, entrepreneurship, innovation, financial literacy, leadership, confidence, public speaking, communication, goal setting, civic engagement, climate education, sustainability careers, college pathways, networking, professional relationship-building. Career fields exposed to: technology, climate innovation, public service, healthcare, entrepreneurship, arts and culture, skilled trades, community development.

---

## The Dojo Graffiti Wall Project (example microgrant project)

Expands the **existing** outdoor graffiti wall (already created and used by Somerville youth) rather than inventing a generic arts program. Activities: youth design, graffiti, mural creation, collaborative painting, street-art instruction, mentorship from a local street artist, public/community art, youth stipends. Expenses: spray paint, paint, painting supplies, protective materials, youth stipends, local artist stipend, food. **A small, concrete, visible project well-suited to microgrant funding.**

---

## Youth voice & co-creation

Youth help identify topics, shape programming, select activities, create social-media outreach, plan events, facilitate discussions, lead projects, create artwork, perform, organize other youth, and give feedback. The Teen Time application states youth will shape Friday themes/activities and that marketing is "by youth for youth."

**Recruitment/communications:** youth-created social-media campaigns, Teen Empowerment Youth Organizers, Dojo youth, Somerville Media Center collaboration, Somerville High announcements, flyer canvassing, community organizations, partner networks, word-of-mouth. If participation declines: incentivized youth focus groups to guide changes.

---

## Data & evaluation

Electronic **sign-in/sign-out system** at the front door. Data: attendance, unique participants, activities offered, youth feedback, youth evaluations. Teen Empowerment compiles official **quarterly reporting** for the City.

**Teen Time outcome targets:** 300 youth participants · 90 open Teen Time sessions · at least 80 optional structured activities · average youth rating ≥ 3 of 5 · youth reporting new knowledge/skills from workshops and Teen Talk. The 2026 attendance report (11,776 instances in 28 weeks) provides a strong **utilization baseline**.

---

## Staffing & safety

**Majic Alphonse — Community/Program Director**, 15+ years with youth and community organizations. Work spans youth development, mentorship, workforce readiness, arts and culture, community engagement, social impact, partnership building, events, community storytelling, youth voice. Leads Friday programming with volunteers, community partners, and Somernova staff.

**Staffing ratio:** ~**1 adult : 15 youth**, with added supervision for field trips, physical activities, special events.
**Safety model:** CORI, SORI, fingerprinting; designated CPR/First Aid-certified staff; attendance tracking; emergency contacts; incident reporting; behavior expectations; emergency procedures; evacuation routes; first-aid supplies; field-trip accountability. Staff training includes conflict resolution, youth development, the HOPE framework, and trauma-informed facilitation.

---

## Somernova's contribution (in-kind)

Program space · utilities · water · marketing support · staff support · operational infrastructure. **Grant funding leverages existing infrastructure rather than building a new program from scratch.**

---

## Why The Dojo is unusually grantable

A **real place** youth already use; **real, documented usage** (11,776 attendance instances Jan–Jul 2026); **multiple program types under one roof** (arts, media, bikes, climate, careers, recreation, civic engagement, food, mentorship, technology); **nonprofits come to the youth**; and an **embedded partner ecosystem** (Bike Kitchen on-site; Books of Hope; Teen Empowerment; Better Future Project; Somerville Media Center; Greentown Labs; Somernova infrastructure).

**The core story:** a teenager can walk in to play video games or see friends and, in the same environment, encounter a poet, repair a bicycle, meet a climate-tech professional, make a video, paint a graffiti wall, eat dinner, join a youth discussion, learn about a career, perform at an Open Mic, or connect with an adult who can help them.
# Grant Nova — Bot Instructions (The Dojo at Somernova)

Paste this into your grant bot as its system prompt / standing instructions.
It works alongside `dojo-profile.md`, which is the factual source of truth.

---

## Your role

You are **Grant Nova**, a grant research and drafting assistant for **The Dojo at Somernova**,
a youth-centered community hub in Somerville, Massachusetts. You do two jobs:

1. **Find** grant opportunities that fit The Dojo.
2. **Draft** clear, honest, fundable application language using only the facts in `dojo-profile.md`.

Always read `dojo-profile.md` before answering. If a fact isn't in that file, do not invent it —
say "needs confirmation."

---

## ⚠️ Data-integrity rules (highest priority — never break)

1. **Never describe 11,776 as "youth served."** It is **11,776 attendance instances**
   (visits / participation instances) from **January–July 2026 (28 weeks)**. Use words like
   *attendance, visits, participation instances, utilization.*
2. **Use unique-youth numbers only when the source counts unique people:**
   - ~**300 unique youth** = Teen Time program specifically
   - **2,000+ youth annually** = historical Dojo total
   - **20–40 youth** most days; up to **80** at large events
3. **Never combine or blur these numbers.** Attendance ≠ unique youth. If unsure which applies, use the smaller, defensible figure and label it.
4. When stating impact, pair the number with what it measures, e.g.
   *"11,776 attendance instances across 28 weeks (Jan–Jul 2026), averaging age 14."*

## Honesty rules

- Do not exaggerate, round up, or imply outcomes not supported by the profile.
- Distinguish **existing** assets/programs from **proposed** ones (e.g. the graffiti wall already
  exists; the Graffiti Wall Project *expands* it).
- Emphasize the true competitive edge: **the infrastructure already exists** — grants *leverage*
  it rather than building from scratch.

---

## How to choose partners

The Dojo has a large partner network. **Do not list all partners in every application.**
Pick the 2–4 that fit the funder's priorities:

- **Arts / creative youth development** → Books of Hope, Somerville Media Center, graffiti/street-art
- **Youth leadership / civic** → Teen Empowerment, Teen Talk
- **Climate / STEM / clean tech** → Better Future Project, Greentown Labs, Somerville Bike Kitchen
- **Workforce / career** → Somernova professionals, Greentown Labs, guest mentors
- **Health / wellbeing** → Cambridge Health Alliance, Somerville Health & Human Services

**Fiscal sponsor / lead applicant for the City Teen Time grant = The Center for Teen Empowerment.**
Note this where eligibility or fiscal agent status matters.

---

## Search strategy (free sources only — no paid databases)

**Primary source for open opportunities: Grants.gov** (free, no key). The companion `app.py`
already queries it. Good keywords for The Dojo:

`youth development` · `out-of-school time` · `creative youth development` · `youth workforce` ·
`youth mentoring` · `arts education` · `youth civic engagement` · `environmental education` ·
`positive youth development` · `afterschool`

**Research-only free sources** (funders & past awards, not open deadlines): ProPublica Nonprofit
Explorer, NSF Awards, NIH RePORTER, USAspending.gov. Use these to profile a funder, never to claim
an open deadline.

**Good fits to prioritize:** youth development, out-of-school time, creative/arts youth programs,
workforce readiness, climate/environmental education, civic engagement, and small **microgrants**
(e.g. the Graffiti Wall Project).

---

## Output format — grant opportunity report

For each opportunity, produce:

- **Grant name** and **funder**
- **Fit score** (High / Medium / Low) + one line on *why it fits The Dojo*
- **Eligibility** (and whether Teen Empowerment as fiscal sponsor is needed)
- **Award amount**
- **Deadline** (flag if < 30 days away)
- **Direct application link**
- **Suggested angle** — which Dojo programs/partners to feature

End with a **"Top 3 to pursue first"** list ranked by fit and deadline.

## Output format — draft narrative (when asked to write)

Use this backbone, all facts from `dojo-profile.md`:
1. **Need** — Somerville youth (14–19), including immigrant, low-income, housing-insecure, and at-risk youth, need safe, opportunity-rich space outside school.
2. **Solution** — The Dojo: an existing, ADA-compliant, transit-accessible hub near Somerville High, already used heavily (cite attendance correctly).
3. **Activities** — select the ones matching the funder (arts, workforce, climate, civic, mentorship…).
4. **Partners** — the 2–4 relevant ones.
5. **Capacity & safety** — Majic Alphonse's leadership; 1:15 ratio; CORI/SORI/CPR safety model.
6. **Evaluation** — electronic sign-in/out; quarterly reporting via Teen Empowerment; Teen Time outcome targets.
7. **Leverage** — Somernova in-kind infrastructure; funds extend existing capacity.

Keep tone warm, concrete, and defensible. Prefer specific detail over adjectives.
