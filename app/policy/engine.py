from enum import Enum

from pydantic import BaseModel


class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ActionDecision(BaseModel):
    action: str
    risk_level: RiskLevel
    requires_approval: bool
    allowed: bool
    reason: str


class PolicyEngine:

    ACTION_POLICIES = {
        "restart_service": {
            "risk_level": RiskLevel.LOW,
            "requires_approval": False,
            "allowed": True,
        },
        "increase_connection_pool": {
            "risk_level": RiskLevel.MEDIUM,
            "requires_approval": True,
            "allowed": True,
        },
        "rollback_deployment": {
            "risk_level": RiskLevel.MEDIUM,
            "requires_approval": True,
            "allowed": True,
        },
        "restart_database": {
            "risk_level": RiskLevel.HIGH,
            "requires_approval": True,
            "allowed": True,
        },
        "delete_database": {
            "risk_level": RiskLevel.CRITICAL,
            "requires_approval": True,
            "allowed": False,
        },
    }

    def evaluate(self, action: str) -> ActionDecision:

        policy = self.ACTION_POLICIES.get(action)

        if policy is None:
            return ActionDecision(
                action=action,
                risk_level=RiskLevel.CRITICAL,
                requires_approval=True,
                allowed=False,
                reason="Unknown actions are blocked by default.",
            )

        return ActionDecision(
            action=action,
            risk_level=policy["risk_level"],
            requires_approval=policy["requires_approval"],
            allowed=policy["allowed"],
            reason=self._build_reason(
                action,
                policy["risk_level"],
                policy["requires_approval"],
                policy["allowed"],
            ),
        )

    def _build_reason(
        self,
        action: str,
        risk_level: RiskLevel,
        requires_approval: bool,
        allowed: bool,
    ) -> str:

        if not allowed:
            return (
                f"Action '{action}' is blocked because it is "
                "considered too dangerous for autonomous execution."
            )

        if requires_approval:
            return (
                f"Action '{action}' is allowed but requires "
                f"human approval because its risk level is "
                f"{risk_level.value}."
            )

        return (
            f"Action '{action}' is considered {risk_level.value} "
            "risk and may be executed automatically."
        )