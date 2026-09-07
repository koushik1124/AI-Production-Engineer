from datetime import datetime

from app.evidence.sources import (
    EventsSource,
    LogsSource,
    MetricsSource,
)


class EvidenceCollector:

    def __init__(self):
        self.metrics_source = MetricsSource()
        self.logs_source = LogsSource()
        self.events_source = EventsSource()

    def collect(self) -> dict:
        """
        Capture a point-in-time snapshot of production evidence.
        """

        captured_at = datetime.now().isoformat(
            timespec="seconds"
        )

        metrics = self.metrics_source.collect()
        logs = self.logs_source.collect()
        events = self.events_source.collect()

        return {
            "captured_at": captured_at,
            "metrics": metrics,
            "logs": logs,
            "events": events,
        }