# ============================================================
# File: src/db/seed_data.py
# Version: 1.1.0
# Created: 2026-06-25
# Modified: 2026-06-25
# Description: Idempotent database seeder — reads org profile Markdown, inserts DB records.
#              Accepts --profile arg to load different org profiles (multi-org capable).
# Usage: python src/db/seed_data.py [--profile data/org_profile/org_profile_seed_data.md]
# ============================================================

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# Ensure project root is on sys.path when run directly
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from sqlalchemy.orm import Session

from src.db.database import SessionLocal, init_db
from src.db.org_profile_loader import load as load_profile
from src.models.funder import Funder, FunderType
from src.models.organization import Organization
from src.models.selection_criteria import SelectionCriteria
from src.models.template import Template
from src.utils.logger import get_logger

log = get_logger(__name__)


# ─── DEFAULT SELECTION CRITERIA ────────────────────────────────────────────────
# These are system defaults and are NOT org-specific (no need to put in Markdown)
DEFAULT_CRITERIA = [
    {
        "name": "Massachusetts / Greater Boston Geography",
        "type": "geography",
        "weight": 8,
        "is_hard_filter": False,
        "config": {"target_geographies": ["Massachusetts", "Greater Boston", "Somerville", "MA"]},
    },
    {
        "name": "Youth Development Focus",
        "type": "focus_area",
        "weight": 9,
        "is_hard_filter": False,
        "config": {
            "target_focus_areas": [
                "Youth Development", "Out-of-School Time", "After School",
                "Youth Programs", "Youth Services",
            ]
        },
    },
    {
        "name": "STEM / STEAM Focus",
        "type": "focus_area",
        "weight": 8,
        "is_hard_filter": False,
        "config": {
            "target_focus_areas": [
                "STEM", "STEAM", "Robotics", "Coding", "Engineering",
                "Science", "Technology", "Computer Science",
            ]
        },
    },
    {
        "name": "Workforce Development Focus",
        "type": "focus_area",
        "weight": 7,
        "is_hard_filter": False,
        "config": {
            "target_focus_areas": [
                "Workforce Development", "Economic Mobility", "Career Readiness",
                "Job Training", "Internship", "Employment",
            ]
        },
    },
    {
        "name": "Climate / Environmental Focus",
        "type": "focus_area",
        "weight": 7,
        "is_hard_filter": False,
        "config": {
            "target_focus_areas": [
                "Climate Education", "Environmental Justice", "Clean Energy",
                "Sustainability", "Climate Tech", "Climate Literacy",
            ]
        },
    },
    {
        "name": "Arts, Culture & Creative Expression",
        "type": "focus_area",
        "weight": 6,
        "is_hard_filter": False,
        "config": {
            "target_focus_areas": [
                "Arts", "Culture", "Music", "Hip-Hop", "Creative Expression", "Arts & Culture",
            ]
        },
    },
    {
        "name": "Eligibility (501c3 or Fiscal Sponsor)",
        "type": "eligibility",
        "weight": 10,
        "is_hard_filter": True,
        "config": {},
    },
    {
        "name": "Grant Amount Range",
        "type": "amount_range",
        "weight": 5,
        "is_hard_filter": False,
        "config": {"min_acceptable": 5000, "max_acceptable": 500000},
    },
]


# ─── DEFAULT PARAGRAPH TEMPLATES (Section 10) ─────────────────────────────────
DEFAULT_TEMPLATES = [
    {
        "name": "Mission Alignment — Youth Development",
        "category": "Mission Alignment",
        "body": (
            "{{org_name}} is a youth-centered community program based in {{city}}, {{state}}, "
            "serving {{target_population}}. Our mission is {{mission}} We believe that every young "
            "person deserves access to safe, structured, and affirming spaces that nurture their "
            "potential and connect them to real-world pathways."
        ),
        "variables_json": ["org_name", "city", "state", "target_population", "mission"],
        "word_count_target": 75,
    },
    {
        "name": "Mission Alignment — Equity & Access",
        "category": "Mission Alignment",
        "body": (
            "{{org_name}} centers equity and multicultural inclusion in all of our programming. "
            "We serve {{target_population}} in {{city}}, with particular focus on low-income youth, "
            "first-generation students, multilingual households, and youth underrepresented in STEM "
            "and career pathways. Our approach is youth-led, community-rooted, and grounded in the "
            "lived experiences of the young people we serve."
        ),
        "variables_json": ["org_name", "target_population", "city"],
        "word_count_target": 80,
    },
    {
        "name": "Need Statement — Somerville Youth",
        "category": "Need Statement",
        "body": (
            "In {{city}}, over 4,900 students are enrolled in public schools, with more than 40% "
            "considered economically disadvantaged. Over 50 languages are spoken in Somerville "
            "schools, reflecting a richly diverse but often under-resourced population. Youth in "
            "our community face significant challenges: limited access to structured out-of-school "
            "programming, gaps in STEM exposure, mental health pressures, and limited career "
            "awareness. {{org_name}} was created to directly address these gaps."
        ),
        "variables_json": ["city", "org_name"],
        "word_count_target": None,
    },
    {
        "name": "Need Statement — STEM Access Gap",
        "category": "Need Statement",
        "body": (
            "Young people in underserved Greater Boston communities face persistent barriers to "
            "STEM education and career exposure. Without structured access to robotics, coding, "
            "and engineering experiences in their youth, these students are systematically excluded "
            "from the fastest-growing sectors of the economy. {{org_name}} is closing this gap "
            "through hands-on STEM programming, peer mentorship, and direct connections to local "
            "STEM employers."
        ),
        "variables_json": ["org_name"],
        "word_count_target": None,
    },
    {
        "name": "Population Served",
        "category": "Population Served",
        "body": (
            "{{org_name}} serves {{target_population}} in {{city}} and Greater Boston, with a "
            "primary focus on low-income youth, first-generation students, multilingual learners, "
            "and youth seeking mentorship and career exposure. We prioritize young people who face "
            "structural barriers to academic and economic success, and we actively recruit and "
            "retain youth from historically underrepresented communities in STEM, clean energy, "
            "and the creative economy."
        ),
        "variables_json": ["org_name", "target_population", "city"],
        "word_count_target": None,
    },
    {
        "name": "Program Description — STEM Explorers",
        "category": "Program Description",
        "body": (
            "{{org_name}}'s STEM Explorers program engages {{target_population}} in hands-on "
            "robotics, coding, engineering challenges, and maker projects. Through partnerships "
            "with DLAB, SHS Robotics, and local universities, participants gain real-world STEM "
            "skills, exposure to STEM careers, and mentorship from professionals in the field. "
            "Youth complete structured projects and are connected to STEM internship and "
            "scholarship opportunities."
        ),
        "variables_json": ["org_name", "target_population"],
        "word_count_target": None,
    },
    {
        "name": "Program Description — Climate Leaders Academy",
        "category": "Program Description",
        "body": (
            "{{org_name}}'s Climate Leaders Academy equips {{target_population}} with climate "
            "literacy, environmental justice education, and hands-on sustainability projects. "
            "In partnership with the Better Future Project, Greentown Labs, and the Somerville "
            "Bike Kitchen, youth learn about clean energy careers, conduct community action "
            "projects, and develop the knowledge and skills to be climate advocates in their "
            "communities."
        ),
        "variables_json": ["org_name", "target_population"],
        "word_count_target": None,
    },
    {
        "name": "Program Description — Workforce Ready",
        "category": "Program Description",
        "body": (
            "{{org_name}}'s Workforce Ready program prepares {{target_population}} for the job "
            "market through resume building, mock interviews, career exploration, and job readiness "
            "workshops. Youth receive stipends for participation, are matched with mentors from "
            "local industries, and are connected to internship opportunities with partner "
            "employers. This program directly addresses career awareness gaps and supports "
            "economic mobility for Greater Boston youth."
        ),
        "variables_json": ["org_name", "target_population"],
        "word_count_target": None,
    },
    {
        "name": "Evaluation Plan",
        "category": "Evaluation Plan",
        "body": (
            "{{org_name}} tracks program outcomes through a combination of attendance tracking, "
            "participant surveys, and goal-attainment records. Key metrics include: youth enrolled "
            "and retained, STEM workshops completed, career workshops attended, mentorship matches "
            "made, internship placements secured, and self-reported measures of confidence, "
            "belonging, and career awareness. Data is collected at program entry, mid-year, and "
            "program exit, and reviewed quarterly by program staff."
        ),
        "variables_json": ["org_name"],
        "word_count_target": None,
    },
    {
        "name": "Budget Narrative",
        "category": "Budget Narrative",
        "body": (
            "The requested funds from {{funder_name}} will support {{program_name}} at "
            "{{org_name}}. Funds will be used for: personnel (program staff and youth stipends), "
            "program supplies and materials, workshop facilitation costs, field trip and event "
            "expenses, and a portion of operational overhead. All expenditures will be tracked "
            "and reported per the funder's requirements, with full financial records available "
            "upon request."
        ),
        "variables_json": ["funder_name", "program_name", "org_name"],
        "word_count_target": None,
    },
    {
        "name": "Sustainability Plan",
        "category": "Sustainability Plan",
        "body": (
            "{{org_name}} is committed to the long-term sustainability of {{program_name}}. We "
            "are actively pursuing a diversified funding base including: foundation grants, "
            "government funding, individual donors, earned revenue from workshops and events, "
            "and in-kind partnerships. We are also pursuing our 501(c)(3) designation, which "
            "will expand our eligibility for a wider range of grant funding. Current partnerships "
            "with {{partner_names}} provide in-kind resources that reduce program costs."
        ),
        "variables_json": ["org_name", "program_name", "partner_names"],
        "word_count_target": None,
    },
    {
        "name": "Organization Capacity",
        "category": "Organization Capacity",
        "body": (
            "{{org_name}} has demonstrated the ability to deliver high-quality, consistent "
            "programming for {{target_population}} in {{city}}. Our team brings expertise in "
            "youth development, STEM education, workforce readiness, and community organizing. "
            "We maintain strong partnerships with {{partner_names}}, which provide additional "
            "capacity, expertise, and resources. Our organizational infrastructure includes "
            "established record-keeping, participant tracking systems, and a track record of "
            "responsible financial management."
        ),
        "variables_json": ["org_name", "target_population", "city", "partner_names"],
        "word_count_target": None,
    },
    {
        "name": "Youth Voice & Leadership",
        "category": "Youth Voice",
        "body": (
            "Youth voice is central to {{org_name}}'s program design. Young people are not simply "
            "recipients of our programming — they are co-designers, peer leaders, and advocates. "
            "Youth participate in program planning, provide feedback on curriculum, serve as "
            "near-peer mentors, and are compensated for leadership roles through our stipend "
            "program. This approach ensures that programming remains relevant, engaging, and "
            "responsive to the actual needs and interests of the communities we serve."
        ),
        "variables_json": ["org_name"],
        "word_count_target": None,
    },
    {
        "name": "Community Partnerships",
        "category": "Partnerships",
        "body": (
            "{{org_name}} has built a robust network of community partners who contribute "
            "expertise, resources, and opportunities to our youth. Current partners include: "
            "Better Future Project (climate education), Greentown Labs (clean energy career "
            "exposure), DLAB (STEM and robotics), SHS Robotics (peer robotics mentorship), "
            "Elizabeth Peabody House (community services), Teen Empowerment (youth leadership), "
            "and Somerville Bike Kitchen (sustainability and community engagement). These "
            "partnerships amplify our reach and deepen the quality of youth experiences."
        ),
        "variables_json": ["org_name"],
        "word_count_target": None,
    },
]


# ─── SEEDING FUNCTIONS ─────────────────────────────────────────────────────────

def _seed_organization(db: Session, profile: dict) -> Organization:
    existing = db.query(Organization).filter_by(name=profile["name"]).first()
    if existing:
        log.info("Organization '%s' already exists — skipping.", profile["name"])
        return existing

    eligibility = profile.get("eligibility", {})
    org = Organization(
        name=profile["name"],
        mission=profile["mission"],
        values_text=profile.get("values_text", ""),
        programs_json=json.dumps(profile.get("programs", []), ensure_ascii=False),
        eligibility_json=json.dumps(eligibility, ensure_ascii=False),
        city=profile.get("city"),
        state=profile.get("state"),
        website=profile.get("website"),
    )
    db.add(org)
    db.flush()
    log.info("Seeded organization: %s (id=%s)", org.name, org.id)
    return org


def _seed_criteria(db: Session) -> SelectionCriteria:
    existing = db.query(SelectionCriteria).filter_by(name="Standard", is_active=True).first()
    if existing:
        log.info("SelectionCriteria 'Standard' already exists — skipping.")
        return existing

    criteria = SelectionCriteria(
        name="Standard",
        version="1.0",
        is_active=True,
        criteria_json=json.dumps(DEFAULT_CRITERIA, ensure_ascii=False),
    )
    db.add(criteria)
    db.flush()
    log.info("Seeded SelectionCriteria: Standard (id=%s)", criteria.id)
    return criteria


def _seed_funder(db: Session, funder_data: dict) -> Funder | None:
    name = funder_data.get("name", "").strip()
    if not name:
        return None

    existing = db.query(Funder).filter_by(name=name).first()
    if existing:
        log.debug("Funder '%s' already exists — skipping.", name)
        return existing

    funder_type_str = funder_data.get("funder_type", "foundation")
    try:
        funder_type = FunderType(funder_type_str)
    except ValueError:
        log.warning("Unknown funder_type '%s' for '%s' — defaulting to 'other'.", funder_type_str, name)
        funder_type = FunderType.OTHER

    funder = Funder(
        name=name,
        funder_type=funder_type,
        is_fiscal_sponsor=bool(funder_data.get("is_fiscal_sponsor", False)),
        is_501c3=bool(funder_data.get("is_501c3", False)),
        relationship_notes=funder_data.get("relationship_notes"),
        priority_tier=funder_data.get("priority_tier"),
    )
    db.add(funder)
    db.flush()
    log.info("Seeded funder: %s (id=%s)", funder.name, funder.id)
    return funder


def _seed_templates(db: Session) -> int:
    count = 0
    for tmpl_data in DEFAULT_TEMPLATES:
        existing = db.query(Template).filter_by(name=tmpl_data["name"], is_system=True).first()
        if existing:
            log.debug("Template '%s' already exists — skipping.", tmpl_data["name"])
            continue

        tmpl = Template(
            name=tmpl_data["name"],
            category=tmpl_data["category"],
            body=tmpl_data["body"],
            variables_json=json.dumps(tmpl_data.get("variables_json", []), ensure_ascii=False),
            word_count_target=tmpl_data.get("word_count_target"),
            is_system=True,
            is_active=True,
            version="1.0",
        )
        db.add(tmpl)
        count += 1

    if count:
        db.flush()
        log.info("Seeded %d paragraph templates.", count)
    return count


def seed(profile_path: str = "data/org_profile/org_profile_seed_data.md") -> None:
    """
    Main seeding entry point. Idempotent — safe to run multiple times.
    """
    log.info("Starting database seed (profile=%s).", profile_path)
    profile = load_profile(profile_path)

    db = SessionLocal()
    try:
        _seed_organization(db, profile)
        _seed_criteria(db)

        for funder_data in profile.get("priority_funders", []):
            _seed_funder(db, funder_data)

        for partner_data in profile.get("community_partners", []):
            _seed_funder(db, partner_data)

        _seed_templates(db)

        db.commit()
        log.info("Database seed complete.")
    except Exception:
        db.rollback()
        log.exception("Seed failed — transaction rolled back.")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Seed the GMAS database.")
    parser.add_argument(
        "--profile",
        default="data/org_profile/org_profile_seed_data.md",
        help="Path to the org profile Markdown file.",
    )
    args = parser.parse_args()

    init_db()  # Create tables if they don't exist (for first run before alembic)
    seed(profile_path=args.profile)
