import json

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.models.incident import Incident, IncidentSeverity
from app.models.incident_db import IncidentDB
from app.evidence.collector import EvidenceCollector
from app.simulator.production import production_state
from app.audit.timeline import timeline
from app.executor.actions import ActionExecutor


router = APIRouter(
    prefix="/simulator",
    tags=["Simulator"],
)


@router.get("/metrics")
async def get_metrics():
    return production_state.get_metrics()


@router.get("/logs")
async def get_logs():
    return {
        "logs": production_state.get_logs()
    }


def get_next_simulator_incident_id(
    db: Session,
) -> str:
    """
    Generate the next sequential simulator incident ID.

    Example:
    INC-SIM-001
    INC-SIM-002
    INC-SIM-003
    """

    incidents = (
        db.query(IncidentDB)
        .filter(
            IncidentDB.id.like("INC-SIM-%")
        )
        .all()
    )

    highest_number = 0

    for incident in incidents:
        try:
            number = int(
                incident.id.split("-")[-1]
            )

            highest_number = max(
                highest_number,
                number,
            )

        except ValueError:
            continue

    next_number = highest_number + 1

    return f"INC-SIM-{next_number:03d}"


@router.post("/failures/database")
def simulate_database_failure(
    db: Session = Depends(get_db),
):
    # Start a completely fresh failure scenario.
    production_state.simulate_database_failure()

    # Capture evidence immediately after
    # the failure is injected.
    collector = EvidenceCollector()
    evidence = collector.collect()

    metrics = evidence["metrics"]
    logs = evidence["logs"]
    events = evidence["events"]
    captured_at = evidence["captured_at"]

    # Generate a NEW incident ID.
    incident_id = get_next_simulator_incident_id(
        db
    )

    incident = Incident(
        id=incident_id,
        service=production_state.service,
        severity=IncidentSeverity.HIGH,
        title="Database connection pool exhausted",
        description=(
            "Database connection pool exhaustion detected "
            "in the production simulator."
        ),
    )

    db_incident = IncidentDB(
        id=incident.id,
        service=incident.service,
        severity=incident.severity.value,
        status=incident.status.value,
        title=incident.title,
        description=incident.description,
        created_at=incident.created_at,
        metrics_snapshot=json.dumps(
            {
                "captured_at": captured_at,
                "data": metrics,
            }
        ),
        logs_snapshot=json.dumps(
            {
                "captured_at": captured_at,
                "data": logs,
            }
        ),
        events_snapshot=json.dumps(
            {
                "captured_at": captured_at,
                "data": events,
            }
        ),
    )

    db.add(db_incident)
    db.commit()
    db.refresh(db_incident)

    # Record the creation in the persistent timeline.
    timeline.record(
        db,
        incident.id,
        "INCIDENT_CREATED",
        f"Incident created: {incident.title}",
    )

    return {
        "message": (
            "Database failure simulated and "
            "new incident created"
        ),
        "incident": incident,
        "evidence": evidence,
    }


@router.post("/failures/redis")
def simulate_redis_failure(
    db: Session = Depends(get_db),
):
    # Start a completely fresh Redis failure scenario.
    production_state.simulate_redis_failure()

    # Capture evidence immediately after
    # the failure is injected.
    collector = EvidenceCollector()
    evidence = collector.collect()

    metrics = evidence["metrics"]
    logs = evidence["logs"]
    events = evidence["events"]
    captured_at = evidence["captured_at"]

    # Generate a NEW incident ID.
    incident_id = get_next_simulator_incident_id(
        db
    )

    incident = Incident(
        id=incident_id,
        service=production_state.service,
        severity=IncidentSeverity.HIGH,
        title="Redis service unavailable",
        description=(
            "Redis became unhealthy in the production "
            "simulator, causing cache failures and "
            "increased application latency."
        ),
    )

    db_incident = IncidentDB(
        id=incident.id,
        service=incident.service,
        severity=incident.severity.value,
        status=incident.status.value,
        title=incident.title,
        description=incident.description,
        created_at=incident.created_at,
        metrics_snapshot=json.dumps(
            {
                "captured_at": captured_at,
                "data": metrics,
            }
        ),
        logs_snapshot=json.dumps(
            {
                "captured_at": captured_at,
                "data": logs,
            }
        ),
        events_snapshot=json.dumps(
            {
                "captured_at": captured_at,
                "data": events,
            }
        ),
    )

    db.add(db_incident)
    db.commit()
    db.refresh(db_incident)

    # Record the creation in the persistent timeline.
    timeline.record(
        db,
        incident.id,
        "INCIDENT_CREATED",
        f"Incident created: {incident.title}",
    )

    return {
        "message": (
            "Redis failure simulated and "
            "new incident created"
        ),
        "incident": incident,
        "evidence": evidence,
    }


@router.post("/failures/deployment")
def simulate_deployment_failure(
    db: Session = Depends(get_db),
):
    # Start a completely fresh deployment regression scenario.
    production_state.simulate_deployment_failure()

    # Capture evidence immediately after
    # the failure is injected.
    collector = EvidenceCollector()
    evidence = collector.collect()

    metrics = evidence["metrics"]
    logs = evidence["logs"]
    events = evidence["events"]
    captured_at = evidence["captured_at"]

    # Generate a NEW incident ID.
    incident_id = get_next_simulator_incident_id(
        db
    )

    incident = Incident(
        id=incident_id,
        service=production_state.service,
        severity=IncidentSeverity.HIGH,
        title="Deployment regression detected",
        description=(
            "A recent application deployment introduced "
            "elevated errors and latency in the production "
            "simulator."
        ),
    )

    db_incident = IncidentDB(
        id=incident.id,
        service=incident.service,
        severity=incident.severity.value,
        status=incident.status.value,
        title=incident.title,
        description=incident.description,
        created_at=incident.created_at,
        metrics_snapshot=json.dumps(
            {
                "captured_at": captured_at,
                "data": metrics,
            }
        ),
        logs_snapshot=json.dumps(
            {
                "captured_at": captured_at,
                "data": logs,
            }
        ),
        events_snapshot=json.dumps(
            {
                "captured_at": captured_at,
                "data": events,
            }
        ),
    )

    db.add(db_incident)
    db.commit()
    db.refresh(db_incident)

    # Record the creation in the persistent timeline.
    timeline.record(
        db,
        incident.id,
        "INCIDENT_CREATED",
        f"Incident created: {incident.title}",
    )

    return {
        "message": (
            "Deployment failure simulated and "
            "new incident created"
        ),
        "incident": incident,
        "evidence": evidence,
    }


@router.post("/reset")
async def reset_simulator():
    production_state.reset()

    return {
        "message": "Production simulator reset",
        "metrics": production_state.get_metrics(),
    }


@router.post("/tests/block-dangerous-action/{incident_id}")
def inject_dangerous_action(
    incident_id: str,
    db: Session = Depends(get_db),
):
    incident = (
        db.query(IncidentDB)
        .filter(IncidentDB.id == incident_id)
        .first()
    )

    if incident is None:
        raise HTTPException(
            status_code=404,
            detail="Incident not found.",
        )

    if incident.status != "waiting_approval":
        raise HTTPException(
            status_code=400,
            detail=(
                "Dangerous-action injection is only allowed "
                "for incidents waiting for approval."
            ),
        )

    incident.recommended_action_type = "delete_database"
    incident.recommended_action = (
        "Delete the production database."
    )

    db.commit()
    db.refresh(incident)

    return {
        "incident_id": incident.id,
        "status": incident.status,
        "recommended_action": incident.recommended_action,
        "recommended_action_type": (
            incident.recommended_action_type
        ),
    }


@router.post("/failures/verification")
def trigger_verification_failure():
    production_state.simulate_recovery_failure()

    return {
        "message": "Verification failure injected successfully.",
        "metrics": production_state.get_metrics(),
        "logs": production_state.get_logs(),
        "events": production_state.events,
    }