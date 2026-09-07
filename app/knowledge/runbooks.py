RUNBOOKS = [
    {
        "id": "RB-001",
        "title": "Database Connection Pool Exhaustion",
        "service": "payment-api",
        "description": (
            "Operational procedure for investigating and responding "
            "to database connection pool exhaustion."
        ),
        "symptoms": [
            "Database connection pool exhausted",
            "Database connection timeout",
            "High error rate",
            "High request latency",
            "Database connection utilization near maximum",
        ],
        "diagnostic_steps": [
            "Check database connection pool utilization.",
            "Compare db_connections_used with db_connections_max.",
            "Confirm whether the database itself is healthy.",
            "Check application logs for connection timeout errors.",
            "Check application logs for connection pool exhaustion.",
        ],
        "remediation_steps": [
            "Increase the database connection pool limit within approved limits.",
            "Monitor connection utilization after the change.",
            "Verify error rate and latency return to acceptable levels.",
        ],
        "verification_checks": [
            "Error rate is at or below 10%.",
            "Latency is at or below 500 ms.",
            "Database connection pool utilization is below 90%.",
            "Database health check passes.",
        ],
        "allowed_actions": [
            "increase_connection_pool",
        ],
    },
    {
        "id": "RB-002",
        "title": "Redis Service Failure",
        "service": "payment-api",
        "description": (
            "Operational procedure for investigating and responding "
            "to Redis service unavailability."
        ),
        "symptoms": [
            "Redis connection refused",
            "Redis unavailable",
            "Cache lookup failed",
            "High error rate",
            "High request latency",
            "Failed to retrieve session data from Redis",
        ],
        "diagnostic_steps": [
            "Check Redis health status.",
            "Check application logs for Redis connection errors.",
            "Check application logs for cache lookup failures.",
            "Confirm whether the database is healthy.",
            "Confirm whether the issue is isolated to Redis.",
        ],
        "remediation_steps": [
            "Restart the Redis service.",
            "Monitor error rate and latency after the restart.",
            "Verify Redis health check passes.",
        ],
        "verification_checks": [
            "Error rate is at or below 10%.",
            "Latency is at or below 500 ms.",
            "Redis health check passes.",
        ],
        "allowed_actions": [
            "restart_service",
        ],
    },
]


def get_runbooks() -> list[dict]:
    return RUNBOOKS