import json
import re

from sqlalchemy.orm import Session

from app.models.incident_db import IncidentDB


class IncidentRetriever:
    """
    Retrieves previously resolved incidents that are relevant
    to the current incident.

    This is intentionally a simple structured retrieval layer.
    We are not using embeddings or a vector database yet.
    """

    STOPWORDS = {
        "a",
        "an",
        "and",
        "are",
        "as",
        "at",
        "be",
        "by",
        "for",
        "from",
        "has",
        "have",
        "in",
        "is",
        "it",
        "of",
        "on",
        "or",
        "that",
        "the",
        "this",
        "to",
        "was",
        "were",
        "with",
    }

    GENERIC_TERMS = {
        "api",
        "detected",
        "error",
        "healthy",
        "production",
        "process",
        "simulator",
        "true",
        "false",
        "service",
        "metrics",
        "logs",
        "events",
        "rate",
        "used",
        "max",
    }

    def retrieve(
        self,
        db: Session,
        current_incident: dict,
        evidence: dict,
        limit: int = 3,
    ) -> list[dict]:

        historical_incidents = (
            db.query(IncidentDB)
            .filter(
                IncidentDB.status == "resolved",
                IncidentDB.id != current_incident.get("id"),
            )
            .all()
        )

        current_text = self._build_current_text(
            current_incident,
            evidence,
        )

        current_tokens = self._tokenize(current_text)

        scored_incidents = []

        for incident in historical_incidents:
            historical_text = self._build_historical_text(incident)
            historical_tokens = self._tokenize(historical_text)

            overlap = current_tokens.intersection(historical_tokens)

            if not overlap:
                continue

            score = len(overlap)

            if incident.service == current_incident.get("service"):
                score += 5

            scored_incidents.append(
                (
                    score,
                    incident,
                    overlap,
                )
            )

        scored_incidents.sort(
            key=lambda item: item[0],
            reverse=True,
        )

        results = []

        for score, incident, overlap in scored_incidents[:limit]:
            results.append(
                {
                    "incident_id": incident.id,
                    "service": incident.service,
                    "title": incident.title,
                    "description": incident.description,
                    "root_cause": incident.investigation_root_cause,
                    "evidence": self._parse_json_list(
                        incident.investigation_evidence
                    ),
                    "impact": incident.investigation_impact,
                    "confidence": incident.investigation_confidence,
                    "recommended_action": incident.recommended_action,
                    "recommended_action_type": (
                        incident.recommended_action_type
                    ),
                    "match_score": score,
                    "matching_terms": sorted(overlap),
                }
            )

        return results

    def _build_current_text(
        self,
        incident: dict,
        evidence: dict,
    ) -> str:

        return " ".join(
            [
                str(incident.get("service", "")),
                str(incident.get("title", "")),
                str(incident.get("description", "")),
                json.dumps(evidence.get("metrics", {})),
                json.dumps(evidence.get("logs", [])),
                json.dumps(evidence.get("events", [])),
            ]
        )

    def _build_historical_text(
        self,
        incident: IncidentDB,
    ) -> str:

        return " ".join(
            [
                str(incident.service),
                str(incident.title),
                str(incident.description),
                str(incident.investigation_root_cause or ""),
                str(incident.investigation_impact or ""),
                str(incident.recommended_action or ""),
                str(incident.recommended_action_type or ""),
                json.dumps(
                    self._parse_json_list(
                        incident.investigation_evidence
                    )
                ),
            ]
        )

    def _tokenize(self, text: str) -> set[str]:
        tokens = re.findall(
            r"[a-z][a-z0-9_-]*",
            text.lower(),
        )

        return {
            token
            for token in tokens
            if token not in self.STOPWORDS
            and token not in self.GENERIC_TERMS
            and len(token) > 2
        }

    def _parse_json_list(
        self,
        value: str | None,
    ) -> list[str]:

        if not value:
            return []

        try:
            parsed = json.loads(value)

            if isinstance(parsed, list):
                return [
                    str(item)
                    for item in parsed
                ]

        except (json.JSONDecodeError, TypeError):
            pass

        return []