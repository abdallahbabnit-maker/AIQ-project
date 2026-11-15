from enum import Enum
from uuid import uuid4
from datetime import datetime, timezone

class ApprovalStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    CHANGES_REQUESTED = "changes_requested"

class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

SENSITIVE_ACTIONS = {
    "publish_content", "execute_payment", "purchase_service",
    "external_api_write", "deploy", "send_email", "modify_credentials",
}
ALWAYS_REQUIRES_APPROVAL = {RiskLevel.HIGH, RiskLevel.CRITICAL}

class ApprovalGate:
    def __init__(self, approval_repo, audit):
        self.approval_repo = approval_repo
        self.audit = audit

    def requires_approval(self, action: str, risk: RiskLevel) -> bool:
        return risk in ALWAYS_REQUIRES_APPROVAL or action in SENSITIVE_ACTIONS

    async def request(self, *, task_id, agent_id, action, risk, payload, requested_by):
        if not self.requires_approval(action, risk):
            await self.audit.log("approval.auto_allowed", task_id=task_id, agent_id=agent_id)
            return {"approved": True, "auto": True, "approval_id": None}
        approval = {
            "id": str(uuid4()), "task_id": task_id, "agent_id": agent_id,
            "action": action, "risk": risk.value, "payload": payload,
            "status": ApprovalStatus.PENDING.value, "requested_by": requested_by,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        await self.approval_repo.create(approval)
        await self.audit.log("approval.requested", task_id=task_id, agent_id=agent_id,
                             detail={"approval_id": approval["id"], "action": action, "risk": risk.value})
        return {"approved": False, "auto": False, "approval_id": approval["id"],
                "status": ApprovalStatus.PENDING.value}
