from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class IncidentSeverity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class IncidentStatus(str, Enum):
    DETECTED = "detected"
    INVESTIGATING = "investigating"
    DIAGNOSING = "diagnosing"
    RECOMMENDING = "recommending"
    WAITING_APPROVAL = "waiting_approval"
    EXECUTING = "executing"
    VERIFYING = "verifying"
    RESOLVED = "resolved"


class Incident(BaseModel):
    id: str
    service: str
    severity: IncidentSeverity
    status: IncidentStatus = IncidentStatus.DETECTED
    title: str
    description: str
    created_at: datetime = Field(
        default_factory=datetime.utcnow
    )

    model_config = {
        "from_attributes": True
    }


class IncidentDetails(Incident):
    investigation_root_cause: str | None = None

    investigation_evidence: list[str] = Field(
        default_factory=list
    )

    investigation_impact: str | None = None

    investigation_confidence: float | None = Field(
        default=None,
        ge=0.0,
        le=1.0,
    )

    recommended_action: str | None = None

    recommended_action_type: str | None = None


class IncidentListItem(Incident):
    investigation_confidence: float | None = Field(
        default=None,
        ge=0.0,
        le=1.0,
    )


class InvestigationResult(BaseModel):
    root_cause: str
    evidence: list[str]
    impact: str
    confidence: float = Field(
        ge=0.0,
        le=1.0,
    )
    next_recommended_action: str
    recommended_action_type: str