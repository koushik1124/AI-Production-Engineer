from datetime import datetime

from pydantic import BaseModel
from sqlalchemy import DateTime, String, Text
from sqlalchemy.orm import Mapped, mapped_column, Session

from app.database.database import Base


class TimelineEventDB(Base):
    __tablename__ = "timeline_events"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True,
    )

    incident_id: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )

    event_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    message: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    timestamp: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
    )


class TimelineEvent(BaseModel):
    incident_id: str
    event_type: str
    message: str
    timestamp: datetime

    model_config = {
        "from_attributes": True
    }


class IncidentTimeline:
    def record(
        self,
        db: Session,
        incident_id: str,
        event_type: str,
        message: str,
    ) -> TimelineEvent:
        event = TimelineEventDB(
            incident_id=incident_id,
            event_type=event_type,
            message=message,
            timestamp=datetime.utcnow(),
        )

        db.add(event)
        db.commit()
        db.refresh(event)

        return TimelineEvent.model_validate(event)

    def get_events(
        self,
        db: Session,
        incident_id: str,
    ) -> list[TimelineEvent]:
        events = (
            db.query(TimelineEventDB)
            .filter(
                TimelineEventDB.incident_id == incident_id
            )
            .order_by(TimelineEventDB.timestamp.asc())
            .all()
        )

        return [
            TimelineEvent.model_validate(event)
            for event in events
        ]

    def delete_events(
        self,
        db: Session,
        incident_id: str,
    ) -> int:
        events = (
            db.query(TimelineEventDB)
            .filter(
                TimelineEventDB.incident_id == incident_id
            )
            .all()
        )

        deleted_count = len(events)

        for event in events:
            db.delete(event)

        # Important:
        # Do not commit here.
        #
        # The incident DELETE endpoint commits both
        # timeline events and the incident together
        # as one transaction.

        return deleted_count


timeline = IncidentTimeline()