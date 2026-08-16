# ============================================================
# File: src/templates/checklists/default_checklist_items.py
# Version: 1.1.0
# Created: 2026-06-25
# Modified: 2026-06-25
# Description: Default checklist item definitions for all 4 review types
#              Used by ReviewService.initialize_checklists()
# ============================================================

from __future__ import annotations

from src.models.review import ReviewType

# Each item: { "text": str, "is_critical": bool }
DEFAULT_CHECKLIST_ITEMS: dict[str, list[dict]] = {
    ReviewType.FACT_VERIFICATION: [
        {
            "text": (
                "Every statistic cited has a named source document in the org library "
                "or a publicly verifiable source"
            ),
            "is_critical": True,
        },
        {
            "text": "All program names match exactly those in the organization profile",
            "is_critical": True,
        },
        {
            "text": (
                "All dates, capacities, and participant counts are verifiable "
                "against org documents"
            ),
            "is_critical": True,
        },
        {
            "text": (
                "No program outcomes are claimed that are not documented in the org "
                "profile or past reports"
            ),
            "is_critical": True,
        },
        {
            "text": "All geographic references are accurate (city, region, service area)",
            "is_critical": False,
        },
        {
            "text": "No staff titles, bios, or credentials are misrepresented",
            "is_critical": False,
        },
    ],

    ReviewType.ASSUMPTION_LOG: [
        {
            "text": (
                "I have reviewed the entire draft and logged every assumption made "
                "in the form below"
            ),
            "is_critical": True,
        },
    ],

    ReviewType.AMBIGUITY_RESOLUTION: [
        {
            "text": (
                "I have reviewed the grant instructions and logged every ambiguity "
                "encountered and how it was resolved"
            ),
            "is_critical": True,
        },
    ],

    ReviewType.COMPLIANCE: [
        {
            "text": "All required narrative sections are completed",
            "is_critical": True,
        },
        {
            "text": "Word or character limits are respected for each section",
            "is_critical": True,
        },
        {
            "text": (
                "All required attachments are prepared and listed in the document "
                "requirements checklist"
            ),
            "is_critical": True,
        },
        {
            "text": "Budget format matches the funder's stated requirements",
            "is_critical": True,
        },
        {
            "text": (
                "The application is submitted by the correct entity (org or fiscal sponsor, "
                "as required)"
            ),
            "is_critical": True,
        },
        {
            "text": "All funder-specific questions are answered in full",
            "is_critical": True,
        },
        {
            "text": "No prohibited content is included (per any funder-stated restrictions)",
            "is_critical": False,
        },
        {
            "text": (
                "Content is aligned with the Dojo's legal, ethical, and organizational policies"
            ),
            "is_critical": True,
        },
    ],
}
