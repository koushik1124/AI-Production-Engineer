from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class ProductionState:
    service: str = "payment-api"

    database_healthy: bool = True
    redis_healthy: bool = True
    payment_gateway_healthy: bool = True

    requests_per_minute: int = 100
    error_rate: float = 0.01
    latency_ms: int = 120

    db_connections_used: int = 20
    db_connections_max: int = 100

    logs: list[str] = field(default_factory=list)
    events: list[str] = field(default_factory=list)

    def reset(self):
        self.database_healthy = True
        self.redis_healthy = True
        self.payment_gateway_healthy = True

        self.requests_per_minute = 100
        self.error_rate = 0.01
        self.latency_ms = 120

        self.db_connections_used = 20
        self.db_connections_max = 100

        self.logs.clear()
        self.events.clear()

    def simulate_database_failure(self):
        """
        Start a fresh database connection-pool
        failure scenario.

        Each simulation represents a new production
        failure and therefore starts with clean logs,
        events, and healthy baseline metrics.
        """

        # Always start from a clean production state.
        self.reset()

        # Inject the failure.
        self.error_rate = 0.37
        self.latency_ms = 2500
        self.db_connections_used = self.db_connections_max

        timestamp = datetime.now().isoformat(
            timespec="seconds"
        )

        # Generate only the evidence belonging
        # to this failure.
        self.logs.extend(
            [
                f"{timestamp} ERROR {self.service} "
                "Database connection timeout",

                f"{timestamp} ERROR {self.service} "
                "Failed to process payment: connection pool exhausted",

                f"{timestamp} ERROR {self.service} "
                "Database connection pool exhausted",
            ]
        )

        self.events.append(
            f"{timestamp} Database connection pool exhausted"
        )

    def simulate_redis_failure(self):
        """
        Start a fresh Redis failure scenario.

        Redis becomes unhealthy, causing cache failures,
        increased error rate, and increased latency.
        """

        # Always start from a clean production state.
        self.reset()

        # Inject the Redis failure.
        self.redis_healthy = False
        self.error_rate = 0.22
        self.latency_ms = 1200

        timestamp = datetime.now().isoformat(
            timespec="seconds"
        )

        # Generate Redis-specific evidence.
        self.logs.extend(
            [
                f"{timestamp} ERROR {self.service} "
                "Redis connection refused",

                f"{timestamp} ERROR {self.service} "
                "Cache lookup failed: Redis unavailable",

                f"{timestamp} ERROR {self.service} "
                "Failed to retrieve session data from Redis",
            ]
        )

        self.events.append(
            f"{timestamp} Redis became unhealthy"
        )

    def simulate_recovery_failure(self):
        """
        Deliberately keep the production environment unhealthy.

        This is a controlled test scenario used to verify that
        the verification engine does not incorrectly mark an
        incident as resolved.
        """

        self.error_rate = 0.25
        self.latency_ms = 1800

        self.events.append(
            "Controlled verification failure injected."
        )

    def get_metrics(self) -> dict:
        return {
            "service": self.service,
            "requests_per_minute": self.requests_per_minute,
            "error_rate": self.error_rate,
            "latency_ms": self.latency_ms,
            "db_connections_used": self.db_connections_used,
            "db_connections_max": self.db_connections_max,
            "database_healthy": self.database_healthy,
            "redis_healthy": self.redis_healthy,
            "payment_gateway_healthy": self.payment_gateway_healthy,
        }

    def get_logs(self) -> list[str]:
        return list(self.logs)


production_state = ProductionState()