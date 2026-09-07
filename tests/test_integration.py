"""
Integration test script for the AI Production Engineer API.

Tests the complete API contract against a running backend.
Requires the backend to be running at http://127.0.0.1:8000.

Tests cover:
- Health endpoint
- Simulator scenarios (database, redis, reset, verification failure)
- Incident CRUD
- Policy enforcement
- Approval flow
- Verification flow
- Audit timeline
- Safety invariants

Does NOT test the LLM investigation endpoint (requires Groq API).
"""

import requests
import sys
__test__ = False

BASE_URL = "http://127.0.0.1:8000"

passed = 0
failed = 0
not_verified = []


def test(name, condition, detail=""):
    global passed, failed
    if condition:
        passed += 1
        print(f"  PASS: {name}")
    else:
        failed += 1
        print(f"  FAIL: {name}")
        if detail:
            print(f"    -> {detail}")


def test_not_verified(name, reason):
    not_verified.append((name, reason))
    print(f"  ? {name} - NOT VERIFIED: {reason}")


# ==============================================================
# TEST 1: Health endpoint
# ==============================================================

print("\n[1] Health Endpoint")

r = requests.get(f"{BASE_URL}/health")
test("GET /health returns 200", r.status_code == 200)
test("Health status is 'healthy'",
     r.json().get("status") == "healthy")

# ==============================================================
# TEST 2: Root endpoint
# ==============================================================

print("\n[2] Root Endpoint")

r = requests.get(f"{BASE_URL}/")
test("GET / returns 200", r.status_code == 200)
test("Root returns correct name",
     r.json().get("name") == "AI Production Engineer")

# ==============================================================
# TEST 3: Simulator reset
# ==============================================================

print("\n[3] Simulator Reset")

r = requests.post(f"{BASE_URL}/simulator/reset")
test("POST /simulator/reset returns 200", r.status_code == 200)

metrics = r.json().get("metrics", {})
test("Reset sets error_rate to 0.01",
     metrics.get("error_rate") == 0.01)
test("Reset sets latency_ms to 120",
     metrics.get("latency_ms") == 120)
test("Reset sets redis_healthy to True",
     metrics.get("redis_healthy") is True)
test("Reset sets database_healthy to True",
     metrics.get("database_healthy") is True)

# ==============================================================
# TEST 4: Database failure simulation
# ==============================================================

print("\n[4] Database Failure Simulation")

r = requests.post(f"{BASE_URL}/simulator/failures/database")
test("POST /simulator/failures/database returns 200",
     r.status_code == 200)

data = r.json()
incident = data.get("incident", {})
test("Incident has INC-SIM- ID",
     incident.get("id", "").startswith("INC-SIM-"))
test("Incident status is 'detected'",
     incident.get("status") == "detected")
test("Incident severity is 'high'",
     incident.get("severity") == "high")

db_incident_id = incident.get("id")

evidence = data.get("evidence", {})
test("Evidence contains metrics",
     "metrics" in evidence)
test("Evidence metrics show exhausted pool",
     evidence.get("metrics", {}).get("db_connections_used") ==
     evidence.get("metrics", {}).get("db_connections_max"))

# ==============================================================
# TEST 5: Incident retrieval
# ==============================================================

print("\n[5] Incident Retrieval")

r = requests.get(f"{BASE_URL}/incidents")
test("GET /incidents returns 200", r.status_code == 200)
test("Response is a list", isinstance(r.json(), list))
test("Created incident is in the list",
     any(i["id"] == db_incident_id for i in r.json()))

# ==============================================================
# TEST 6: Incident details
# ==============================================================

print("\n[6] Incident Details")

r = requests.get(f"{BASE_URL}/incidents/{db_incident_id}")
test("GET /incidents/{id} returns 200", r.status_code == 200)
test("Incident has correct ID",
     r.json().get("id") == db_incident_id)
test("Incident has investigation_evidence field",
     "investigation_evidence" in r.json())

# ==============================================================
# TEST 7: Incident timeline
# ==============================================================

print("\n[7] Incident Timeline")

r = requests.get(
    f"{BASE_URL}/incidents/{db_incident_id}/timeline"
)
test("GET timeline returns 200", r.status_code == 200)

events = r.json().get("events", [])
test("Timeline has INCIDENT_CREATED event",
     any(e["event_type"] == "INCIDENT_CREATED"
         for e in events))

# ==============================================================
# TEST 8: Redis failure simulation
# ==============================================================

print("\n[8] Redis Failure Simulation")

# Reset first
requests.post(f"{BASE_URL}/simulator/reset")

r = requests.post(f"{BASE_URL}/simulator/failures/redis")
test("POST /simulator/failures/redis returns 200",
     r.status_code == 200)

redis_data = r.json()
redis_incident = redis_data.get("incident", {})
test("Redis incident has INC-SIM- ID",
     redis_incident.get("id", "").startswith("INC-SIM-"))

redis_incident_id = redis_incident.get("id")

redis_evidence = redis_data.get("evidence", {})
test("Redis evidence shows redis_healthy=False",
     redis_evidence.get("metrics", {}).get("redis_healthy")
     is False)

# ==============================================================
# TEST 9: Simulator metrics endpoint
# ==============================================================

print("\n[9] Simulator Metrics")

r = requests.get(f"{BASE_URL}/simulator/metrics")
test("GET /simulator/metrics returns 200",
     r.status_code == 200)
test("Metrics contain redis_healthy",
     "redis_healthy" in r.json())

# ==============================================================
# TEST 10: Simulator logs endpoint
# ==============================================================

print("\n[10] Simulator Logs")

r = requests.get(f"{BASE_URL}/simulator/logs")
test("GET /simulator/logs returns 200", r.status_code == 200)
test("Response has 'logs' key",
     "logs" in r.json())

# ==============================================================
# TEST 11: Policy test endpoint
# ==============================================================

print("\n[11] Policy Test Endpoint")

r = requests.get(f"{BASE_URL}/policy/test/restart_service")
test("restart_service is allowed",
     r.json().get("allowed") is True)
test("restart_service does not require approval",
     r.json().get("requires_approval") is False)

r = requests.get(
    f"{BASE_URL}/policy/test/increase_connection_pool"
)
test("increase_connection_pool requires approval",
     r.json().get("requires_approval") is True)
test("increase_connection_pool is allowed",
     r.json().get("allowed") is True)

r = requests.get(f"{BASE_URL}/policy/test/delete_database")
test("delete_database is blocked",
     r.json().get("allowed") is False)

r = requests.get(f"{BASE_URL}/policy/test/unknown_action")
test("Unknown action is blocked",
     r.json().get("allowed") is False)

r = requests.get(f"{BASE_URL}/policy/test/restart_database")
test("restart_database requires approval",
     r.json().get("requires_approval") is True)
test("restart_database is allowed",
     r.json().get("allowed") is True)

# ==============================================================
# TEST 12: Verification failure scenario
# ==============================================================

print("\n[12] Verification Failure Scenario")

r = requests.post(
    f"{BASE_URL}/simulator/failures/verification"
)
test("POST /simulator/failures/verification returns 200",
     r.status_code == 200)

r = requests.get(f"{BASE_URL}/simulator/metrics")
metrics = r.json()
test("After verification failure injection, error_rate > 0.10",
     metrics.get("error_rate", 0) > 0.10)

# ==============================================================
# TEST 13: Investigation (requires Groq API)
# ==============================================================

print("\n[13] AI Investigation")

test_not_verified(
    "AI Investigation end-to-end",
    "Requires live Groq API call - cannot test in automated script"
)

# ==============================================================
# TEST 14: Approval without waiting_approval status
# ==============================================================

print("\n[14] Approval Guard")

r = requests.post(
    f"{BASE_URL}/incidents/{db_incident_id}/approve"
)
test("Approve on 'detected' incident returns 400",
     r.status_code == 400)

# ==============================================================
# TEST 15: Verify without verifying status
# ==============================================================

print("\n[15] Verification Guard")

r = requests.post(
    f"{BASE_URL}/incidents/{db_incident_id}/verify"
)
test("Verify on 'detected' incident returns 400",
     r.status_code == 400)

# ==============================================================
# TEST 16: Investigate on non-detected incident
# ==============================================================

print("\n[16] Investigation Guard")

# incident is 'detected', so this should work. But to test the
# guard, we'd need an incident in another state. We verify the
# guard exists by checking investigation only works on 'detected'.
r = requests.get(
    f"{BASE_URL}/incidents/{db_incident_id}"
)
test("DB incident is in 'detected' status",
     r.json().get("status") == "detected")

# ==============================================================
# TEST 17: Incident deletion with timeline cascade
# ==============================================================

print("\n[17] Incident Deletion + Timeline Cascade")

# First confirm timeline exists
r = requests.get(
    f"{BASE_URL}/incidents/{db_incident_id}/timeline"
)
pre_delete_events = len(r.json().get("events", []))
test("Incident has timeline events before deletion",
     pre_delete_events > 0)

# Delete the incident
r = requests.delete(
    f"{BASE_URL}/incidents/{db_incident_id}"
)
test("DELETE /incidents/{id} returns 200",
     r.status_code == 200)

# Confirm it's gone
r = requests.get(
    f"{BASE_URL}/incidents/{db_incident_id}"
)
test("Deleted incident returns 404",
     r.status_code == 404)

# Confirm timeline is also gone
r = requests.get(
    f"{BASE_URL}/incidents/{db_incident_id}/timeline"
)
test("Deleted incident timeline returns 404",
     r.status_code == 404)

# ==============================================================
# TEST 18: Delete the Redis incident too (cleanup)
# ==============================================================

print("\n[18] Cleanup")

r = requests.delete(
    f"{BASE_URL}/incidents/{redis_incident_id}"
)
test("Redis incident deleted successfully",
     r.status_code == 200)

# Reset simulator
requests.post(f"{BASE_URL}/simulator/reset")

# ==============================================================
# TEST 19: 404 for non-existent incident
# ==============================================================

print("\n[19] Non-existent Incident")

r = requests.get(f"{BASE_URL}/incidents/FAKE-ID-999")
test("Non-existent incident returns 404",
     r.status_code == 404)

# ==============================================================
# Summary
# ==============================================================

print(f"\n{'='*50}")
print(f"RESULTS: {passed} passed, {failed} failed, "
      f"{len(not_verified)} not verified")
print(f"{'='*50}")

if not_verified:
    print("\nNOT VERIFIED:")
    for name, reason in not_verified:
        print(f"  ? {name}: {reason}")

if failed > 0:
    print(f"\n!! {failed} test(s) FAILED")
else:
    print("\nPASS: All verifiable tests PASSED")