from pydantic import BaseModel

from app.simulator.production import production_state


class ActionResult(BaseModel):
    action: str
    success: bool
    message: str


class ActionExecutor:
    def execute(
        self,
        action: str,
        target_service: str | None = None,
    ) -> ActionResult:

        if action == "increase_connection_pool":
            return self._increase_connection_pool()

        if action == "restart_service":
            return self._restart_service(target_service)

        if action == "rollback_deployment":
            return self._rollback_deployment()

        if action == "restart_database":
            return self._restart_database()

        return ActionResult(
            action=action,
            success=False,
            message=f"Action '{action}' is not registered.",
        )

    def _increase_connection_pool(self) -> ActionResult:
        connection_utilization = (
            production_state.db_connections_used
            / production_state.db_connections_max
        )

        if connection_utilization < 0.90:
            return ActionResult(
                action="increase_connection_pool",
                success=False,
                message="Database connection pool has sufficient capacity.",
            )

        old_limit = production_state.db_connections_max

        production_state.db_connections_max = old_limit + 50

        production_state.db_connections_used = min(
            production_state.db_connections_used,
            production_state.db_connections_max,
        )

        production_state.error_rate = 0.05
        production_state.latency_ms = 400

        production_state.events.append(
            "Database connection pool increased "
            f"from {old_limit} to {production_state.db_connections_max}"
        )

        return ActionResult(
            action="increase_connection_pool",
            success=True,
            message=(
                "Database connection pool increased from "
                f"{old_limit} to {production_state.db_connections_max}."
            ),
        )

    def _restart_service(
        self,
        target_service: str | None = None,
    ) -> ActionResult:

        target = target_service or production_state.service

        # Redis recovery
        if target.lower() == "redis":
            production_state.redis_healthy = True
            production_state.error_rate = 0.01
            production_state.latency_ms = 120

            production_state.events.append(
                "Redis service restarted successfully."
            )

            return ActionResult(
                action="restart_service",
                success=True,
                message="Redis service restarted successfully.",
            )

        # Application service recovery
        production_state.error_rate = 0.01
        production_state.latency_ms = 120
        production_state.redis_healthy = True

        production_state.events.append(
            f"Service '{target}' restarted successfully."
        )

        return ActionResult(
            action="restart_service",
            success=True,
            message=(
                f"Service '{target}' restarted successfully."
            ),
        )

    def _rollback_deployment(self) -> ActionResult:
        production_state.error_rate = 0.01
        production_state.latency_ms = 120

        production_state.events.append(
            "Deployment rolled back successfully."
        )

        return ActionResult(
            action="rollback_deployment",
            success=True,
            message="Deployment rolled back successfully.",
        )

    def _restart_database(self) -> ActionResult:
        production_state.database_healthy = True
        production_state.db_connections_used = 20
        production_state.error_rate = 0.01
        production_state.latency_ms = 120

        production_state.events.append(
            "Database restarted successfully."
        )

        return ActionResult(
            action="restart_database",
            success=True,
            message="Database restarted successfully.",
        )