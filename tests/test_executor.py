"""
Tests for the Action Executor.

Verifies that the executor correctly handles registered
actions, rejects unknown actions, and targets the correct
service for restart_service.
"""

from app.executor.actions import ActionExecutor
from app.simulator.production import production_state


executor = ActionExecutor()


def setup_function():
    """Reset simulator state before each test."""
    production_state.reset()


def test_unknown_action_returns_failure():
    result = executor.execute("delete_database")

    assert result.success is False
    assert "not registered" in result.message.lower()


def test_another_unknown_action_returns_failure():
    result = executor.execute("exec_shell_command")

    assert result.success is False
    assert "not registered" in result.message.lower()


def test_restart_service_default_target():
    result = executor.execute("restart_service")

    assert result.success is True
    assert result.action == "restart_service"


def test_restart_service_targets_redis():
    """
    When target_service is 'redis', the executor must
    restart Redis specifically and not the application.
    """
    production_state.redis_healthy = False

    result = executor.execute(
        "restart_service",
        target_service="redis",
    )

    assert result.success is True
    assert production_state.redis_healthy is True
    assert "redis" in result.message.lower()


def test_increase_connection_pool_when_exhausted():
    production_state.simulate_database_failure()

    result = executor.execute("increase_connection_pool")

    assert result.success is True
    assert production_state.db_connections_max > 100


def test_increase_connection_pool_when_not_needed():
    """
    When the pool has sufficient capacity, the action
    should fail (no remediation needed).
    """
    result = executor.execute("increase_connection_pool")

    assert result.success is False


def test_rollback_deployment():
    result = executor.execute("rollback_deployment")

    assert result.success is True
    assert result.action == "rollback_deployment"


def test_restart_database():
    production_state.database_healthy = False

    result = executor.execute("restart_database")

    assert result.success is True
    assert production_state.database_healthy is True
