from datetime import datetime

from sqlalchemy import DateTime, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database.database import Base


class IncidentDB(Base):
    __tablename__ = "incidents"

    id: Mapped[str] = mapped_column(
        String(50),
        primary_key=True,
    )

    service: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    severity: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )

    status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
    )

    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    description: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
    )

    # Structured production evidence captured at incident creation
    metrics_snapshot: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    logs_snapshot: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    events_snapshot: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    # Investigation results
    investigation_root_cause: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    investigation_evidence: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    investigation_impact: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    investigation_confidence: Mapped[float | None] = mapped_column(
        nullable=True,
    )

    recommended_action: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    recommended_action_type: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )