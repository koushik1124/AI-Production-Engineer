"""
Tests for the InvestigationAgent LLM response cleaner.

Verifies that <think> tags, markdown fences, and
combinations thereof are correctly stripped before
JSON parsing.
"""

import json

import pytest

from app.agents.investigation import InvestigationAgent


def test_clean_plain_json():
    raw = '{"root_cause": "test"}'
    result = InvestigationAgent._clean_llm_response(raw)

    assert json.loads(result) == {"root_cause": "test"}


def test_clean_think_tags():
    raw = (
        "<think>\n"
        "I need to analyze...\n"
        "</think>\n"
        '{"root_cause": "test"}'
    )
    result = InvestigationAgent._clean_llm_response(raw)

    assert json.loads(result) == {"root_cause": "test"}


def test_clean_markdown_json_fence():
    raw = (
        '```json\n'
        '{"root_cause": "test"}\n'
        '```'
    )
    result = InvestigationAgent._clean_llm_response(raw)

    assert json.loads(result) == {"root_cause": "test"}


def test_clean_markdown_plain_fence():
    raw = (
        '```\n'
        '{"root_cause": "test"}\n'
        '```'
    )
    result = InvestigationAgent._clean_llm_response(raw)

    assert json.loads(result) == {"root_cause": "test"}


def test_clean_think_plus_fence():
    raw = (
        "<think>\n"
        "Let me reason about this...\n"
        "</think>\n\n"
        "```json\n"
        '{"root_cause": "test"}\n'
        "```"
    )
    result = InvestigationAgent._clean_llm_response(raw)

    assert json.loads(result) == {"root_cause": "test"}


def test_empty_after_cleaning_raises():
    raw = "<think>only thinking, no output</think>"

    with pytest.raises(ValueError):
        InvestigationAgent._clean_llm_response(raw)


def test_clean_preserves_valid_json_structure():
    raw = (
        "<think>analysis</think>\n"
        '{"root_cause": "x", "evidence": ["a", "b"], '
        '"impact": "y", "confidence": 0.85, '
        '"next_recommended_action": "z", '
        '"recommended_action_type": "restart_service"}'
    )
    result = InvestigationAgent._clean_llm_response(raw)
    data = json.loads(result)

    assert data["confidence"] == 0.85
    assert data["recommended_action_type"] == "restart_service"
    assert len(data["evidence"]) == 2
