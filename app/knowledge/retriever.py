import re

from app.knowledge.runbooks import get_runbooks


class RunbookRetriever:
    """
    Retrieves operational runbooks relevant to the current incident.

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
        "check",
        "current",
        "error",
        "healthy",
        "logs",
        "metrics",
        "production",
        "service",
        "step",
        "steps",
        "system",
        "true",
        "false",
    }

    def retrieve(
        self,
        incident: dict,
        evidence: dict,
        limit: int = 3,
    ) -> list[dict]:

        current_text = self._build_current_text(
            incident,
            evidence,
        )

        current_tokens = self._tokenize(current_text)

        scored_runbooks = []

        for runbook in get_runbooks():
            runbook_text = self._build_runbook_text(runbook)
            runbook_tokens = self._tokenize(runbook_text)

            overlap = current_tokens.intersection(runbook_tokens)

            if not overlap:
                continue

            score = len(overlap)

            if runbook["service"] == incident.get("service"):
                score += 5

            scored_runbooks.append(
                (
                    score,
                    runbook,
                    overlap,
                )
            )

        scored_runbooks.sort(
            key=lambda item: item[0],
            reverse=True,
        )

        results = []

        for score, runbook, overlap in scored_runbooks[:limit]:
            results.append(
                {
                    "runbook_id": runbook["id"],
                    "title": runbook["title"],
                    "service": runbook["service"],
                    "description": runbook["description"],
                    "symptoms": runbook["symptoms"],
                    "diagnostic_steps": runbook["diagnostic_steps"],
                    "remediation_steps": runbook["remediation_steps"],
                    "verification_checks": runbook["verification_checks"],
                    "allowed_actions": runbook["allowed_actions"],
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
                str(evidence.get("metrics", {})),
                str(evidence.get("logs", [])),
                str(evidence.get("events", [])),
            ]
        )

    def _build_runbook_text(
        self,
        runbook: dict,
    ) -> str:

        return " ".join(
            [
                str(runbook.get("title", "")),
                str(runbook.get("service", "")),
                str(runbook.get("description", "")),
                " ".join(runbook.get("symptoms", [])),
                " ".join(runbook.get("diagnostic_steps", [])),
                " ".join(runbook.get("remediation_steps", [])),
                " ".join(runbook.get("verification_checks", [])),
                " ".join(runbook.get("allowed_actions", [])),
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