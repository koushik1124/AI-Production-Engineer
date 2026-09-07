"""
Tests for the Policy Engine.

Verifies that the policy engine correctly classifies actions
by risk level, approval requirements, and allowed status.
"""

from app.policy.engine import PolicyEngine, RiskLevel


engine = PolicyEngine()


def test_restart_service_is_low_risk_and_auto_executable():
    decision = engine.evaluate("restart_service")

    assert decision.allowed is True
    assert decision.requires_approval is False
    assert decision.risk_level == RiskLevel.LOW


def test_increase_connection_pool_requires_approval():
    decision = engine.evaluate("increase_connection_pool")

    assert decision.allowed is True
    assert decision.requires_approval is True
    assert decision.risk_level == RiskLevel.MEDIUM


def test_rollback_deployment_requires_approval():
    decision = engine.evaluate("rollback_deployment")

    assert decision.allowed is True
    assert decision.requires_approval is True
    assert decision.risk_level == RiskLevel.MEDIUM


def test_restart_database_requires_approval():
    decision = engine.evaluate("restart_database")

    assert decision.allowed is True
    assert decision.requires_approval is True
    assert decision.risk_level == RiskLevel.HIGH


def test_delete_database_is_blocked():
    decision = engine.evaluate("delete_database")

    assert decision.allowed is False
    assert decision.risk_level == RiskLevel.CRITICAL


def test_unknown_action_is_blocked():
    decision = engine.evaluate("drop_all_tables")

    assert decision.allowed is False
    assert decision.requires_approval is True
    assert decision.risk_level == RiskLevel.CRITICAL


def test_another_unknown_action_is_blocked():
    decision = engine.evaluate("exec_shell_command")

    assert decision.allowed is False
    assert decision.risk_level == RiskLevel.CRITICAL


def test_empty_string_action_is_blocked():
    decision = engine.evaluate("")

    assert decision.allowed is False
    assert decision.risk_level == RiskLevel.CRITICAL
