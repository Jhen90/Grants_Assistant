# ============================================================
# File: src/discovery/query_expander.py
# Version: 1.2.0
# Created: 2026-06-30
# Modified: 2026-06-30
# Description: Turn one org profile into a comprehensive battery of search
#   queries so discovery "searches everywhere" — every focus area crossed with
#   geography scope, target population, and the current/next grant year.
#   Deterministic: same profile + year always yields the same query set.
# ============================================================

from __future__ import annotations

from datetime import date

# Generic grant phrasings appended to topic+geo combinations.
_GRANT_TERMS = ("grant", "funding", "RFP", "grant opportunity")


def expand_queries(
    org_profile: dict,
    year: int | None = None,
    max_queries: int = 40,
) -> list[str]:
    """
    Build a de-duplicated, capped list of search queries from the org profile.

    Pulls focus areas from programs, geography from city/state (plus broader
    scopes), and the target population, then crosses them with grant phrasings
    for this year and next.
    """
    year = year or date.today().year
    years = [str(year), str(year + 1)]

    focus_areas = _focus_areas(org_profile)
    geographies = _geographies(org_profile)
    population = (org_profile.get("eligibility", {}) or {}).get("target_population", "")
    population_word = "youth" if "youth" in population.lower() else population.strip()

    queries: list[str] = []

    # Topic × geography × year — the core sweep
    for focus in focus_areas:
        for geo in geographies:
            queries.append(f"{focus} grant {geo} {years[0]}")
        # One nonprofit-scoped and one population-scoped variant per focus
        queries.append(f"{focus} grant nonprofit {geographies[0]}")
        if population_word:
            queries.append(f"{population_word} {focus} grant {years[0]}")

    # Population × geography baseline (catches generalist youth funders)
    if population_word:
        for geo in geographies[:3]:
            queries.append(f"{population_word} programs grant {geo} {years[0]}")

    # Org-type / mission-level catch-alls
    for geo in geographies[:2]:
        for term in _GRANT_TERMS[:2]:
            queries.append(f"nonprofit youth development {term} {geo} {years[0]}")

    return _dedupe_cap(queries, max_queries)


def _focus_areas(org_profile: dict) -> list[str]:
    areas: list[str] = []
    for program in org_profile.get("programs", []) or []:
        if isinstance(program, dict):
            fa = (program.get("focus_area") or "").strip()
            if fa and fa.lower() not in [a.lower() for a in areas]:
                areas.append(fa)
    # Sensible defaults if the profile has no programs.
    if not areas:
        areas = ["youth development", "STEM education", "after-school"]
    return areas


def _geographies(org_profile: dict) -> list[str]:
    city = (org_profile.get("city") or "").strip()
    state = (org_profile.get("state") or "").strip()
    scopes: list[str] = []
    if city and state:
        scopes.append(f"{city} {state}")
    if city:
        scopes.append(city)
    if state:
        scopes.append(state)
        # State name spelled out helps web search (e.g. "Massachusetts").
    scopes.append("New England")
    scopes.append("national")
    # De-dup preserving order.
    seen: set[str] = set()
    out: list[str] = []
    for s in scopes:
        if s and s.lower() not in seen:
            seen.add(s.lower())
            out.append(s)
    return out


def _dedupe_cap(queries: list[str], cap: int) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for q in queries:
        norm = " ".join(q.split()).strip()
        key = norm.lower()
        if norm and key not in seen:
            seen.add(key)
            out.append(norm)
        if len(out) >= cap:
            break
    return out
