# Org Profile: The Dojo at Somernova
# ============================================================
# File: data/org_profile/org_profile_seed_data.md
# Version: 1.1.0
# Created: 2026-06-25
# Modified: 2026-06-25
# Description: Structured organization profile for GMAS seed data.
#              GMAS can be configured for any organization by replacing this file.
#              Edit the yaml blocks below. Human-readable sections are for context only.
# Usage: python src/db/seed_data.py [--profile data/org_profile/org_profile_seed_data.md]
# ============================================================

---

## 1 · Organization Identity

```yaml
name: "The Dojo at Somernova"
city: "Somerville"
state: "Massachusetts"
website: ""
```

---

## 2 · Mission & Values

```yaml
mission: >
  The Dojo empowers young people through safe, structured, and youth-centered programming
  that builds leadership, creativity, workforce readiness, and community connection.
  Through mentorship, STEM and climate education, arts and culture, and real-world
  opportunities, we help youth develop the skills, confidence, and networks needed to thrive.

values_text: "Equity · Multicultural Inclusion · Youth Voice · Community Safety · Climate Literacy · Economic Mobility"
```

---

## 3 · Programs

Each program needs: name, focus_area, description.

```yaml
programs:
  - name: "Future Fridays"
    focus_area: "Youth Development"
    description: >
      Weekly drop-in youth program including food, mentorship, guest speakers,
      entrepreneurship, financial literacy, and leadership development.

  - name: "STEM Explorers"
    focus_area: "STEM/STEAM"
    description: >
      Hands-on STEM activities: robotics, coding, engineering challenges, maker
      projects, and STEM career exploration. Partners: DLAB, SHS Robotics, local universities.

  - name: "Climate Leaders Academy"
    focus_area: "Climate Education"
    description: >
      Climate literacy, environmental justice, clean energy careers, sustainability
      projects, and community action. Partners: Better Future Project, Greentown Labs,
      Somerville Bike Kitchen.

  - name: "Workforce Ready"
    focus_area: "Workforce Development"
    description: >
      Resume building, interview skills, career exploration, job readiness, internship
      exposure, and youth stipends.

  - name: "Girls in STEM & Climate Innovation"
    focus_area: "Girls in STEM"
    description: >
      Women mentors, robotics, coding, entrepreneurship, climate technology, and
      leadership development for young women ages 13–18.
```

---

## 4 · Eligibility

```yaml
eligibility:
  has_501c3: false
  default_fiscal_sponsor: "Teen Empowerment"
  default_fiscal_sponsor_is_501c3: true
  fiscal_sponsorship_accepted: true
  target_geographies:
    - "Massachusetts"
    - "Greater Boston"
    - "Somerville"
  target_population: "youth ages 13–18"
  org_type: "Youth Development Organization (Future 501(c)(3))"
```

---

## 5 · Priority Grant Funders

Funders are pre-seeded as known grant-making organizations the Dojo actively pursues.
Fields: name, funder_type, priority_tier, is_501c3, relationship_notes.

```yaml
priority_funders:
  - name: "Cummings Foundation"
    funder_type: "foundation"
    priority_tier: 1
    is_501c3: true
    is_fiscal_sponsor: false
    relationship_notes: "MA-based; priority for general operating support"

  - name: "MassCEC"
    funder_type: "government"
    priority_tier: 1
    is_501c3: true
    is_fiscal_sponsor: false
    relationship_notes: "MA Clean Energy Center; climate and workforce grants"

  - name: "Boston Foundation"
    funder_type: "foundation"
    priority_tier: 1
    is_501c3: true
    is_fiscal_sponsor: false
    relationship_notes: "Greater Boston community grants"

  - name: "Barr Foundation"
    funder_type: "foundation"
    priority_tier: 1
    is_501c3: true
    is_fiscal_sponsor: false
    relationship_notes: "Climate, arts, learning"

  - name: "United Way of Massachusetts Bay"
    funder_type: "foundation"
    priority_tier: 1
    is_501c3: true
    is_fiscal_sponsor: false
    relationship_notes: "Youth development, economic mobility"

  - name: "National Grid Foundation"
    funder_type: "corporate"
    priority_tier: 1
    is_501c3: true
    is_fiscal_sponsor: false
    relationship_notes: "STEM and clean energy"

  - name: "Eversource Energy Foundation"
    funder_type: "corporate"
    priority_tier: 1
    is_501c3: true
    is_fiscal_sponsor: false
    relationship_notes: "STEM and community programs"

  - name: "Mass Cultural Council"
    funder_type: "government"
    priority_tier: 2
    is_501c3: true
    is_fiscal_sponsor: false
    relationship_notes: "Arts and culture programs"

  - name: "Awesome Foundation"
    funder_type: "foundation"
    priority_tier: 2
    is_501c3: true
    is_fiscal_sponsor: false
    relationship_notes: "Small grassroots grants"

  - name: "NEFA"
    funder_type: "foundation"
    priority_tier: 2
    is_501c3: true
    is_fiscal_sponsor: false
    relationship_notes: "New England Foundation for the Arts"

  - name: "Google.org"
    funder_type: "corporate"
    priority_tier: 3
    is_501c3: true
    is_fiscal_sponsor: false
    relationship_notes: "STEM education, workforce development"

  - name: "Microsoft Philanthropies"
    funder_type: "corporate"
    priority_tier: 3
    is_501c3: true
    is_fiscal_sponsor: false
    relationship_notes: "STEM, digital equity"

  - name: "Biogen Foundation"
    funder_type: "corporate"
    priority_tier: 3
    is_501c3: true
    is_fiscal_sponsor: false
    relationship_notes: "STEM education"

  - name: "Vertex Foundation"
    funder_type: "corporate"
    priority_tier: 3
    is_501c3: true
    is_fiscal_sponsor: false
    relationship_notes: "STEM, workforce"

  - name: "Moderna Foundation"
    funder_type: "corporate"
    priority_tier: 3
    is_501c3: true
    is_fiscal_sponsor: false
    relationship_notes: "STEM education and workforce"
```

---

## 6 · Community Partners & Fiscal Sponsors

is_fiscal_sponsor: true means this org can act as fiscal sponsor for the Dojo.
is_501c3: true means this org holds its own 501(c)(3) — required for fiscal sponsorship.
Teen Empowerment is the PRIMARY default fiscal sponsor.

```yaml
community_partners:
  - name: "Teen Empowerment"
    funder_type: "community_partner"
    is_fiscal_sponsor: true
    is_501c3: true
    relationship_notes: "PRIMARY default fiscal sponsor for the Dojo"

  - name: "Elizabeth Peabody House"
    funder_type: "community_partner"
    is_fiscal_sponsor: true
    is_501c3: true
    relationship_notes: "Can serve as fiscal sponsor for youth/community programs"

  - name: "Mystic Learning Center"
    funder_type: "community_partner"
    is_fiscal_sponsor: true
    is_501c3: true
    relationship_notes: "Can serve as fiscal sponsor; education focus"

  - name: "Groundwork Somerville"
    funder_type: "community_partner"
    is_fiscal_sponsor: true
    is_501c3: true
    relationship_notes: "Environmental justice fiscal sponsor for climate programs"

  - name: "Better Future Project"
    funder_type: "community_partner"
    is_fiscal_sponsor: true
    is_501c3: true
    relationship_notes: "Fiscal sponsor option for climate/environmental grants"

  - name: "DLAB"
    funder_type: "community_partner"
    is_fiscal_sponsor: false
    is_501c3: false
    relationship_notes: "STEM partner, not a fiscal sponsor"

  - name: "SHS Robotics"
    funder_type: "community_partner"
    is_fiscal_sponsor: false
    is_501c3: false
    relationship_notes: "STEM partner, not a fiscal sponsor"

  - name: "Greentown Labs"
    funder_type: "community_partner"
    is_fiscal_sponsor: false
    is_501c3: false
    relationship_notes: "Climate/clean energy partner"

  - name: "Somerville Bike Kitchen"
    funder_type: "community_partner"
    is_fiscal_sponsor: false
    is_501c3: false
    relationship_notes: "Sustainability partner"

  - name: "Haitian Coalition"
    funder_type: "community_partner"
    is_fiscal_sponsor: false
    is_501c3: true
    relationship_notes: "Community partner"

  - name: "350 Mass"
    funder_type: "community_partner"
    is_fiscal_sponsor: false
    is_501c3: true
    relationship_notes: "Climate advocacy partner"

  - name: "Boston Tech Poetics"
    funder_type: "community_partner"
    is_fiscal_sponsor: false
    is_501c3: false
    relationship_notes: "Arts/tech partner"

  - name: "Community Power Pedal Group"
    funder_type: "community_partner"
    is_fiscal_sponsor: false
    is_501c3: false
    relationship_notes: "Community partner"

  - name: "SHS Debate"
    funder_type: "community_partner"
    is_fiscal_sponsor: false
    is_501c3: false
    relationship_notes: "Youth leadership partner"

  - name: "Youth Guidance Boston"
    funder_type: "community_partner"
    is_fiscal_sponsor: false
    is_501c3: true
    relationship_notes: "Youth development partner"

  - name: "Young Kings Initiative"
    funder_type: "community_partner"
    is_fiscal_sponsor: false
    is_501c3: false
    relationship_notes: "Youth leadership partner"

  - name: "Youth Artist Incubator"
    funder_type: "community_partner"
    is_fiscal_sponsor: false
    is_501c3: false
    relationship_notes: "Arts partner"
```
