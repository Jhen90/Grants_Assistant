# ============================================================
# File: tests/unit/test_template_renderer.py
# Version: 1.1.0
# Created: 2026-06-25
# ============================================================

import pytest

from src.engine.template_renderer import (
    build_org_context,
    extract_variables,
    render_template,
)
from src.models.organization import Organization


def _make_org(**kwargs) -> Organization:
    org = Organization.__new__(Organization)
    org.name = kwargs.get("name", "The Dojo")
    org.mission = kwargs.get("mission", "Empowering youth through martial arts.")
    org.city = kwargs.get("city", "Boston")
    org.state = kwargs.get("state", "MA")
    org.website = kwargs.get("website", None)
    org.programs_json = kwargs.get("programs_json", "[]")
    org.eligibility_json = kwargs.get("eligibility_json", "{}")
    return org


class TestRenderTemplate:
    def test_simple_substitution(self):
        body = "Hello, {{org_name}}!"
        result = render_template(body, {"org_name": "The Dojo"})
        assert result == "Hello, The Dojo!"

    def test_unknown_variable_gets_placeholder(self):
        body = "Contact: {{contact_email}}"
        result = render_template(body, {})
        assert "[FILL IN:" in result
        assert "contact_email" in result

    def test_multiple_variables(self):
        body = "{{org_name}} is in {{city}}, {{state}}."
        ctx = {"org_name": "Test Org", "city": "Boston", "state": "MA"}
        result = render_template(body, ctx)
        assert result == "Test Org is in Boston, MA."

    def test_empty_template(self):
        result = render_template("", {})
        assert result == ""

    def test_no_variables_unchanged(self):
        body = "This template has no variables."
        result = render_template(body, {"org_name": "Test"})
        assert result == body


class TestExtractVariables:
    def test_extracts_all_variables(self):
        body = "Hello {{name}}, welcome to {{city}}!"
        vars_ = extract_variables(body)
        assert set(vars_) == {"name", "city"}

    def test_deduplicates_variables(self):
        body = "{{name}} and {{name}} again."
        vars_ = extract_variables(body)
        assert vars_.count("name") == 1

    def test_empty_body_returns_empty(self):
        assert extract_variables("") == []


class TestBuildOrgContext:
    def test_returns_dict_with_org_name(self):
        org = _make_org()
        ctx = build_org_context(org)
        assert ctx["org_name"] == "The Dojo"

    def test_returns_city_state(self):
        org = _make_org()
        ctx = build_org_context(org)
        assert ctx["city"] == "Boston"
        assert ctx["state"] == "MA"

    def test_all_values_are_strings(self):
        org = _make_org()
        ctx = build_org_context(org)
        for k, v in ctx.items():
            assert isinstance(v, str), f"Key {k!r} is not a string: {type(v)}"
