from abc import ABC, abstractmethod

from app.simulator.production import production_state


class EvidenceSource(ABC):

    @abstractmethod
    def collect(self):
        """Collect evidence from a production source."""
        pass


class MetricsSource(EvidenceSource):

    def collect(self) -> dict:
        return production_state.get_metrics()


class LogsSource(EvidenceSource):

    def collect(self) -> list[str]:
        return production_state.get_logs()


class EventsSource(EvidenceSource):

    def collect(self) -> list[str]:
        return list(production_state.events)