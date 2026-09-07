import json

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.agents.investigation import InvestigationAgent
from app.audit.timeline import timeline
from app.database.database import get_db
from app.executor.actions import ActionExecutor
from app.knowledge.retriever import RunbookRetriever
from app.models.incident import (
    IncidentDetails,
    IncidentListItem,
    IncidentStatus,
)
from app.models.incident_db import IncidentDB
from app.policy.engine import PolicyEngine
from app.retrieval.incident_retriever import IncidentRetriever
from app.verification.verifier import VerificationEngine


router = APIRouter(
    prefix="/incidents",
    tags=["Incidents"],
)


# ---------------------------------------------------------
# Snapshot helpers
#
# Snapshots are stored as an envelope:
#   {"captured_at": ..., "data": <actual payload>}
# Every reader must unwrap "data" — reading the envelope
# itself as if it were the payload silently returns
# whatever default .get()/or falls back to, which is how
# the redis-vs-payment-api mistargeting bug happened.
# ---------------------------------------------------------

def _unwrap_snapshot(raw_json: str | None, default):
    """
    Parse a stored snapshot column and return its "data"
    payload, or `default` if the column is empty, invalid
    JSON, or missing the "data" key.
    """
    if not raw_json:
        return default

    try:
        parsed = json.loads(raw_json)
    except json.JSONDecodeError:
        return default

    return parsed.get("data", default)


def resolve_restart_target(
    action_type: str,
    incident: IncidentDB,
    metrics: dict,
) -> str | None:
    """
    Single source of truth for deciding what
    'restart_service' should actually target.

    `metrics` must already be the UNWRAPPED metrics
    payload (i.e. the "data" portion of metrics_snapshot),
    not the raw envelope.
    """
    if action_type != "restart_service":
        return None

    if not metrics.get("redis_healthy", True):
        return "redis"

    return incident.service


# ---------------------------------------------------------
# Incident List
# ---------------------------------------------------------

@router.get(
    "",
    response_model=list[IncidentListItem],
)
def get_incidents(
    db: Session = Depends(get_db),
):
    incidents = (
        db.query(IncidentDB)
        .order_by(IncidentDB.created_at.desc())
        .all()
    )

    results = []

    for incident in incidents:
        results.append(
            IncidentListItem(
                id=incident.id,
                service=incident.service,
                severity=incident.severity,
                status=incident.status,
                title=incident.title,
                description=incident.description,
                created_at=incident.created_at,
                investigation_confidence=(
                    incident.investigation_confidence
                ),
            )
        )

    return results


# ---------------------------------------------------------
# Delete Incident
# ---------------------------------------------------------

@router.delete("/{incident_id}")
def delete_incident(
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

    # Delete all timeline events belonging to
    # this incident before deleting the incident itself.
    timeline.delete_events(
        db,
        incident_id,
    )

    db.delete(incident)
    db.commit()

    return {
        "incident_id": incident_id,
        "message": "Incident and timeline deleted successfully.",
    }


# ---------------------------------------------------------
# Incident Timeline
# ---------------------------------------------------------

@router.get("/{incident_id}/timeline")
def get_incident_timeline(
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

    events = timeline.get_events(
        db,
        incident_id,
    )

    return {
        "incident_id": incident_id,
        "events": events,
    }


# ---------------------------------------------------------
# Incident Policy
# ---------------------------------------------------------

@router.get("/{incident_id}/policy")
def get_incident_policy(
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

    action = incident.recommended_action_type

    if not action:
        raise HTTPException(
            status_code=400,
            detail=(
                "No recommended action is available "
                "for this incident."
            ),
        )

    policy_engine = PolicyEngine()

    decision = policy_engine.evaluate(action)

    return decision.model_dump()


# ---------------------------------------------------------
# Incident Details
# ---------------------------------------------------------

@router.get(
    "/{incident_id}",
    response_model=IncidentDetails,
)
def get_incident(
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

    # NOTE: investigation_evidence is a separate field from
    # metrics_snapshot/logs_snapshot/events_snapshot — it's
    # written directly by the investigation agent as a plain
    # list, not wrapped in a {"captured_at", "data"} envelope,
    # so it is intentionally NOT passed through _unwrap_snapshot.
    evidence = []

    if incident.investigation_evidence:
        try:
            evidence = json.loads(
                incident.investigation_evidence
            )
        except json.JSONDecodeError:
            evidence = []

    return IncidentDetails(
        id=incident.id,
        service=incident.service,
        severity=incident.severity,
        status=incident.status,
        title=incident.title,
        description=incident.description,
        created_at=incident.created_at,
        investigation_root_cause=(
            incident.investigation_root_cause
        ),
        investigation_evidence=evidence,
        investigation_impact=(
            incident.investigation_impact
        ),
        investigation_confidence=(
            incident.investigation_confidence
        ),
        recommended_action=(
            incident.recommended_action
        ),
        recommended_action_type=(
            incident.recommended_action_type
        ),
    )


# ---------------------------------------------------------
# AI Investigation
# ---------------------------------------------------------

@router.post("/{incident_id}/investigate")
async def investigate_incident(
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

    if incident.status != IncidentStatus.DETECTED.value:
        raise HTTPException(
            status_code=400,
            detail=(
                "Incident can only be investigated "
                "when its status is 'detected'."
            ),
        )

    # FIXED: unwrap the {"captured_at", "data"} envelope for
    # all three snapshot columns instead of reading them raw.
    evidence = {
        "metrics": _unwrap_snapshot(
            incident.metrics_snapshot, {}
        ),
        "logs": _unwrap_snapshot(
            incident.logs_snapshot, []
        ),
        "events": _unwrap_snapshot(
            incident.events_snapshot, []
        ),
    }

    incident_dict = {
        "id": incident.id,
        "service": incident.service,
        "severity": incident.severity,
        "status": incident.status,
        "title": incident.title,
        "description": incident.description,
        "created_at": incident.created_at.isoformat(),
    }

    incident.status = IncidentStatus.INVESTIGATING.value

    db.commit()
    db.refresh(incident)

    # -----------------------------------------------------
    # Historical Incident Retrieval
    # -----------------------------------------------------

    retriever = IncidentRetriever()

    historical_incidents = retriever.retrieve(
        db=db,
        current_incident=incident_dict,
        evidence=evidence,
        limit=3,
    )

    if historical_incidents:
        timeline.record(
            db,
            incident.id,
            "HISTORICAL_CONTEXT_RETRIEVED",
            (
                "Retrieved "
                f"{len(historical_incidents)} historical "
                "incidents for investigation."
            ),
        )

    # -----------------------------------------------------
    # Runbook / Operational Knowledge Retrieval
    # -----------------------------------------------------

    runbook_retriever = RunbookRetriever()

    runbooks = runbook_retriever.retrieve(
        incident=incident_dict,
        evidence=evidence,
        limit=3,
    )

    if runbooks:
        timeline.record(
            db,
            incident.id,
            "RUNBOOK_CONTEXT_RETRIEVED",
            (
                "Retrieved "
                f"{len(runbooks)} operational runbook(s) "
                "for investigation."
            ),
        )

    # -----------------------------------------------------
    # AI Investigation
    # -----------------------------------------------------

    agent = InvestigationAgent()

    try:
        result = await agent.investigate(
            incident=incident_dict,
            evidence=evidence,
            historical_incidents=historical_incidents,
            runbooks=runbooks,
        )

    except Exception:
        # If AI investigation fails, do not leave the
        # incident permanently stuck in "investigating".
        incident.status = IncidentStatus.DETECTED.value

        db.commit()
        db.refresh(incident)

        raise

    # -----------------------------------------------------
    # Store Investigation Result
    # -----------------------------------------------------

    incident.investigation_root_cause = (
        result.root_cause
    )

    incident.investigation_evidence = json.dumps(
        result.evidence
    )

    incident.investigation_impact = (
        result.impact
    )

    incident.investigation_confidence = (
        result.confidence
    )

    incident.recommended_action = (
        result.next_recommended_action
    )

    incident.recommended_action_type = (
        result.recommended_action_type
    )

    db.commit()
    db.refresh(incident)

    # -----------------------------------------------------
    # Investigation Completed
    # -----------------------------------------------------

    timeline.record(
        db,
        incident.id,
        "INVESTIGATION_COMPLETED",
        (
            "AI investigation completed. "
            f"Recommended action: "
            f"{result.recommended_action_type}"
        ),
    )

    # -----------------------------------------------------
    # Policy Evaluation
    #
    # The AI recommends an action, but the Policy Engine
    # decides whether that action can execute automatically
    # or requires human approval.
    # -----------------------------------------------------

    policy_engine = PolicyEngine()

    policy_decision = policy_engine.evaluate(
        result.recommended_action_type
    )

    # -----------------------------------------------------
    # Blocked Action
    # -----------------------------------------------------

    if not policy_decision.allowed:
        incident.status = IncidentStatus.DETECTED.value

        timeline.record(
            db,
            incident.id,
            "ACTION_BLOCKED",
            (
                "Recommended action was blocked by "
                "the policy engine."
            ),
        )

        db.commit()
        db.refresh(incident)

        return {
            "incident_id": incident.id,
            "status": incident.status,
            "message": (
                "AI investigation completed, but the "
                "recommended action was blocked by policy."
            ),
            "investigation": result.model_dump(),
            "policy_decision": (
                policy_decision.model_dump()
            ),
            "historical_incidents": historical_incidents,
            "runbooks": runbooks,
        }

    # -----------------------------------------------------
    # Human Approval Required
    # -----------------------------------------------------

    if policy_decision.requires_approval:
        incident.status = (
            IncidentStatus.WAITING_APPROVAL.value
        )

        timeline.record(
            db,
            incident.id,
            "APPROVAL_REQUIRED",
            (
                "Human approval required before "
                "executing the recommended action."
            ),
        )

        db.commit()
        db.refresh(incident)

        return {
            "incident_id": incident.id,
            "status": incident.status,
            "message": (
                "AI investigation completed. "
                "Human approval is required."
            ),
            "investigation": result.model_dump(),
            "policy_decision": (
                policy_decision.model_dump()
            ),
            "historical_incidents": historical_incidents,
            "runbooks": runbooks,
        }

    # -----------------------------------------------------
    # Automatic Execution
    #
    # Low-risk actions that are explicitly allowed by
    # policy can execute without human approval.
    # -----------------------------------------------------

    timeline.record(
        db,
        incident.id,
        "AUTO_EXECUTION_APPROVED",
        (
            "Policy engine approved automatic execution "
            "because the action is low risk and does not "
            "require human approval."
        ),
    )

    incident.status = IncidentStatus.EXECUTING.value

    db.commit()
    db.refresh(incident)

    # -----------------------------------------------------
    # Execute Remediation
    # -----------------------------------------------------

    executor = ActionExecutor()

    # FIXED: uses the shared resolver against the already
    # -unwrapped evidence["metrics"] dict.
    target_service = resolve_restart_target(
        result.recommended_action_type,
        incident,
        evidence["metrics"],
    )

    if result.recommended_action_type == "restart_service":
        timeline.record(
            db,
            incident.id,
            "RESTART_TARGET_RESOLVED",
            f"Resolved restart target: {target_service}",
        )

    action_result = executor.execute(
        result.recommended_action_type,
        target_service=target_service,
    )

    if not action_result.success:
        timeline.record(
            db,
            incident.id,
            "ACTION_FAILED",
            action_result.message,
        )

        incident.status = IncidentStatus.DETECTED.value

        db.commit()

        return {
            "incident_id": incident.id,
            "status": incident.status,
            "message": "Automatic action execution failed.",
            "action_result": (
                action_result.model_dump()
            ),
            "policy_decision": (
                policy_decision.model_dump()
            ),
            "investigation": result.model_dump(),
            "historical_incidents": historical_incidents,
            "runbooks": runbooks,
        }

    timeline.record(
        db,
        incident.id,
        "ACTION_EXECUTED",
        action_result.message,
    )

    # -----------------------------------------------------
    # Move to Verification
    #
    # Verification is intentionally NOT performed here.
    # It remains a separate lifecycle stage.
    # -----------------------------------------------------

    incident.status = IncidentStatus.VERIFYING.value

    db.commit()
    db.refresh(incident)

    return {
        "incident_id": incident.id,
        "status": incident.status,
        "message": (
            "AI investigation completed and the "
            "low-risk action was executed automatically. "
            "Incident is ready for recovery verification."
        ),
        "investigation": result.model_dump(),
        "policy_decision": (
            policy_decision.model_dump()
        ),
        "action_result": (
            action_result.model_dump()
        ),
        "historical_incidents": historical_incidents,
        "runbooks": runbooks,
    }


# ---------------------------------------------------------
# Human Approval + Execution
# ---------------------------------------------------------

@router.post("/{incident_id}/approve")
def approve_incident(
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

    if incident.status != IncidentStatus.WAITING_APPROVAL.value:
        raise HTTPException(
            status_code=400,
            detail=(
                "Incident is not waiting for approval."
            ),
        )

    if not incident.recommended_action_type:
        raise HTTPException(
            status_code=400,
            detail=(
                "Incident does not have a "
                "recommended action."
            ),
        )

    # -----------------------------------------------------
    # CRITICAL SAFETY GATE
    #
    # Never trust the frontend approval state.
    # Re-evaluate the policy immediately before execution.
    # -----------------------------------------------------

    policy_engine = PolicyEngine()

    policy_decision = policy_engine.evaluate(
        incident.recommended_action_type
    )

    if not policy_decision.allowed:
        timeline.record(
            db,
            incident.id,
            "ACTION_BLOCKED",
            (
                "Recommended action was blocked by "
                "the policy engine."
            ),
        )

        raise HTTPException(
            status_code=403,
            detail={
                "message": (
                    "Action blocked by policy engine."
                ),
                "policy_decision": (
                    policy_decision.model_dump()
                ),
            },
        )

    if not policy_decision.requires_approval:
        raise HTTPException(
            status_code=400,
            detail={
                "message": (
                    "This action does not require "
                    "human approval."
                ),
                "policy_decision": (
                    policy_decision.model_dump()
                ),
            },
        )

    # -----------------------------------------------------
    # Human Approval
    # -----------------------------------------------------

    timeline.record(
        db,
        incident.id,
        "APPROVED",
        (
            "Human approval received. "
            "Policy re-check passed."
        ),
    )

    # -----------------------------------------------------
    # Execute Remediation
    # -----------------------------------------------------

    incident.status = IncidentStatus.EXECUTING.value

    db.commit()
    db.refresh(incident)

    executor = ActionExecutor()

    # FIXED: use the same shared resolver as
    # investigate_incident, fed with unwrapped metrics
    # instead of the raw snapshot envelope. This replaces
    # the old duplicated try/except block that read
    # metrics_snapshot flat and silently fell through to
    # incident.service on any mismatch.
    metrics = _unwrap_snapshot(
        incident.metrics_snapshot, {}
    )

    target_service = resolve_restart_target(
        incident.recommended_action_type,
        incident,
        metrics,
    )

    if incident.recommended_action_type == "restart_service":
        timeline.record(
            db,
            incident.id,
            "RESTART_TARGET_RESOLVED",
            f"Resolved restart target: {target_service}",
        )

    action_result = executor.execute(
        incident.recommended_action_type,
        target_service=target_service,
    )

    if not action_result.success:
        timeline.record(
            db,
            incident.id,
            "ACTION_FAILED",
            action_result.message,
        )

        incident.status = IncidentStatus.DETECTED.value

        db.commit()

        raise HTTPException(
            status_code=500,
            detail={
                "message": "Action execution failed.",
                "action_result": (
                    action_result.model_dump()
                ),
                "policy_decision": (
                    policy_decision.model_dump()
                ),
            },
        )

    timeline.record(
        db,
        incident.id,
        "ACTION_EXECUTED",
        action_result.message,
    )

    # -----------------------------------------------------
    # Move to Verification
    #
    # Verification is intentionally NOT performed here.
    # It is a separate lifecycle stage.
    # -----------------------------------------------------

    incident.status = IncidentStatus.VERIFYING.value

    db.commit()
    db.refresh(incident)

    return {
        "incident_id": incident.id,
        "status": incident.status,
        "message": (
            "Action executed successfully. "
            "Incident is ready for recovery verification."
        ),
        "action_result": (
            action_result.model_dump()
        ),
        "policy_decision": (
            policy_decision.model_dump()
        ),
    }


# ---------------------------------------------------------
# Recovery Verification
# ---------------------------------------------------------

@router.post("/{incident_id}/verify")
def verify_incident(
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

    if incident.status != IncidentStatus.VERIFYING.value:
        raise HTTPException(
            status_code=400,
            detail=(
                "Incident can only be verified "
                "when its status is 'verifying'."
            ),
        )

    # -----------------------------------------------------
    # Verification Started
    # -----------------------------------------------------

    timeline.record(
        db,
        incident.id,
        "VERIFICATION_STARTED",
        "Production recovery verification started.",
    )

    verifier = VerificationEngine()

    verification = verifier.verify()

    # -----------------------------------------------------
    # Verification Failed
    # -----------------------------------------------------

    if not verification.verified:
        timeline.record(
            db,
            incident.id,
            "VERIFICATION_FAILED",
            (
                "Production recovery verification failed."
            ),
        )

        db.commit()

        return {
            "incident_id": incident.id,
            "status": incident.status,
            "message": (
                "Recovery verification failed. "
                "Incident remains unresolved."
            ),
            "verification": (
                verification.model_dump()
            ),
        }

    # -----------------------------------------------------
    # Verification Passed
    # -----------------------------------------------------

    timeline.record(
        db,
        incident.id,
        "VERIFICATION_COMPLETED",
        "Production recovery verification passed.",
    )

    incident.status = IncidentStatus.RESOLVED.value

    db.commit()
    db.refresh(incident)

    timeline.record(
        db,
        incident.id,
        "INCIDENT_RESOLVED",
        (
            "Incident resolved after successful "
            "remediation and recovery verification."
        ),
    )

    return {
        "incident_id": incident.id,
        "status": incident.status,
        "message": (
            "Incident recovery successfully verified "
            "and incident resolved."
        ),
        "verification": (
            verification.model_dump()
        ),
    }