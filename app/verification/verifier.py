from pydantic import BaseModel

from app.simulator.production import production_state


class VerificationResult(BaseModel):
    verified: bool
    checks: list[str]
    failed_checks: list[str]


class VerificationEngine:

    def verify(self) -> VerificationResult:
        checks = []
        failed_checks = []

        metrics = production_state.get_metrics()

        # Check 1: Error rate
        if metrics["error_rate"] <= 0.10:
            checks.append(
                "Error rate returned to an acceptable range."
            )
        else:
            failed_checks.append(
                f"Error rate is still too high: "
                f"{metrics['error_rate']}"
            )

        # Check 2: Latency
        if metrics["latency_ms"] <= 500:
            checks.append(
                "Latency returned to an acceptable range."
            )
        else:
            failed_checks.append(
                f"Latency is still too high: "
                f"{metrics['latency_ms']} ms"
            )

        # Check 3: Database connection capacity
        connection_utilization = (
            metrics["db_connections_used"]
            / metrics["db_connections_max"]
        )

        if connection_utilization < 0.90:
            checks.append(
                "Database connection pool has sufficient capacity."
            )
        else:
            failed_checks.append(
                "Database connection pool is still near capacity."
            )

        # Check 4: Database health
        if metrics["database_healthy"]:
            checks.append(
                "Database health check passed."
            )
        else:
            failed_checks.append(
                "Database is still reporting as unhealthy."
            )

        # Check 5: Redis health
        if metrics["redis_healthy"]:
            checks.append(
                "Redis health check passed."
            )
        else:
            failed_checks.append(
                "Redis is still reporting as unhealthy."
            )

        return VerificationResult(
            verified=len(failed_checks) == 0,
            checks=checks,
            failed_checks=failed_checks,
        )