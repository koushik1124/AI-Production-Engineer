"""
Tests for the Verification Engine.

Verifies that the verification engine correctly assesses
production health and that failed checks prevent resolution.
"""

from app.simulator.production import production_state
from app.verification.verifier import VerificationEngine


verifier = VerificationEngine()


def setup_function():
    """Reset simulator state before each test."""
    production_state.reset()


def test_healthy_state_passes_verification():
    result = verifier.verify()

    assert result.verified is True
    assert len(result.failed_checks) == 0
    assert len(result.checks) > 0


def test_high_error_rate_fails_verification():
    production_state.error_rate = 0.25

    result = verifier.verify()

    assert result.verified is False
    assert any(
        "error rate" in check.lower()
        for check in result.failed_checks
    )


def test_high_latency_fails_verification():
    production_state.latency_ms = 1800

    result = verifier.verify()

    assert result.verified is False
    assert any(
        "latency" in check.lower()
        for check in result.failed_checks
    )


def test_exhausted_connection_pool_fails_verification():
    production_state.db_connections_used = (
        production_state.db_connections_max
    )

    result = verifier.verify()

    assert result.verified is False
    assert any(
        "connection pool" in check.lower()
        for check in result.failed_checks
    )


def test_unhealthy_database_fails_verification():
    production_state.database_healthy = False

    result = verifier.verify()

    assert result.verified is False
    assert any(
        "database" in check.lower()
        for check in result.failed_checks
    )


def test_unhealthy_redis_fails_verification():
    production_state.redis_healthy = False

    result = verifier.verify()

    assert result.verified is False
    assert any(
        "redis" in check.lower()
        for check in result.failed_checks
    )


def test_multiple_failures_all_reported():
    production_state.error_rate = 0.30
    production_state.latency_ms = 2000
    production_state.redis_healthy = False

    result = verifier.verify()

    assert result.verified is False
    assert len(result.failed_checks) >= 3


def test_recovery_failure_scenario():
    """
    Simulate the controlled verification failure scenario.
    After injecting recovery failure, verification must fail.
    """
    production_state.simulate_recovery_failure()

    result = verifier.verify()

    assert result.verified is False
    assert len(result.failed_checks) > 0


def test_database_failure_then_recovery():
    """
    After a database failure and remediation (increase pool),
    verification should pass.
    """
    production_state.simulate_database_failure()

    # Simulate remediation: increase pool
    production_state.db_connections_max += 50
    production_state.db_connections_used = 20
    production_state.error_rate = 0.05
    production_state.latency_ms = 400

    result = verifier.verify()

    assert result.verified is True
