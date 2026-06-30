# ============================================================
# File: tests/unit/test_aggregator_csv.py
# Version: 1.2.0
# Created: 2026-06-30
# Description: Tests for the ToS-compliant Instrumentl CSV importer.
# ============================================================

from __future__ import annotations

from datetime import date

from src.discovery.sources.aggregator import InstrumentlCsvImporter


def test_csv_import_maps_columns():
    csv_text = (
        "Name,Funder,Deadline,Max Award,URL\n"
        "Youth STEM Fund,Acme Foundation,2026-09-17,50000,https://acme.org/grant\n"
    )
    cands = InstrumentlCsvImporter().import_csv(csv_text)
    assert len(cands) == 1
    c = cands[0]
    assert c.extracted["title"] == "Youth STEM Fund"
    assert c.extracted["funder_name"] == "Acme Foundation"
    assert c.extracted["deadline"] == date(2026, 9, 17)
    assert c.extracted["amount_max"] == 50000.0
    assert c.extracted["source_url"] == "https://acme.org/grant"


def test_csv_skips_rows_without_title():
    csv_text = "Name,Funder\n,Acme Foundation\nReal Grant,Beta Fund\n"
    cands = InstrumentlCsvImporter().import_csv(csv_text)
    assert len(cands) == 1
    assert cands[0].extracted["title"] == "Real Grant"


def test_money_parsing_strips_symbols():
    csv_text = "Title,Max Award\nGrant A,\"$1,250,000\"\n"
    cands = InstrumentlCsvImporter().import_csv(csv_text)
    assert cands[0].extracted["amount_max"] == 1_250_000.0
