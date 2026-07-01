"""Tests for probe loading and evaluation."""

from __future__ import annotations

from agent_acceptance_kit.probes.loader import evaluate_response, list_suites, load_suite
from agent_acceptance_kit.probes.base import ProbeExpectation


def test_list_suites_includes_starters() -> None:
    names = list_suites()
    assert "rag" in names
    assert "tool_use" in names
    assert "coding_agent" in names


def test_load_rag_suite_has_probes() -> None:
    suite = load_suite("rag")
    assert suite.name == "rag"
    assert len(suite.probes) == 3
    assert suite.probes[0].id.startswith("rag-")


def test_evaluate_response_contains() -> None:
    ok, detail = evaluate_response(
        "Retention is 90 days in hot storage.",
        ProbeExpectation(contains=("90 days",)),
    )
    assert ok is True
    assert "met" in detail.lower()


def test_evaluate_response_missing_substring() -> None:
    ok, detail = evaluate_response("no match", ProbeExpectation(contains=("90 days",)))
    assert ok is False
    assert "90 days" in detail
