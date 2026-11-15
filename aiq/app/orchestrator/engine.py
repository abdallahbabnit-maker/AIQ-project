from enum import Enum

class TaskState(str, Enum):
    QUEUED = "queued"
    ASSIGNED = "assigned"
    RUNNING = "running"
    AWAITING_APPROVAL = "awaiting_approval"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"

class PermissionDenied(Exception):
    pass

class Orchestrator:
    def __init__(self, registry, gate, audit, task_repo=None):
        self.registry = registry
        self.gate = gate
        self.audit = audit
        self.task_repo = task_repo

    def select_agent(self, required_skills):
        candidates = [a for a in self.registry.all() if required_skills.issubset(a.skills)]
        if not candidates:
            return None
        return max(candidates, key=lambda a: len(a.skills))

    async def execute(self, task, agent):
        task_id = task["id"]
        await self.audit.log("task.started", task_id=task_id, agent_id=agent.id)
        action = task.get("action", "")
        if action not in agent.allowed_actions:
            await self.audit.log("task.blocked_permission", task_id=task_id, agent_id=agent.id,
                                 detail={"action": action})
            return {"state": TaskState.FAILED.value, "error": "action_not_allowed"}
        from app.orchestrator.approval_gate import RiskLevel
        risk = RiskLevel(task.get("risk", "low"))
        gate_result = await self.gate.request(
            task_id=task_id, agent_id=agent.id, action=action, risk=risk,
            payload=task.get("payload", {}), requested_by=agent.id,
        )
        if not gate_result["approved"]:
            await self.audit.log("task.awaiting_approval", task_id=task_id, agent_id=agent.id,
                                 detail={"approval_id": gate_result["approval_id"]})
            return {"state": TaskState.AWAITING_APPROVAL.value, "approval_id": gate_result["approval_id"]}
        await self.audit.log("task.succeeded", task_id=task_id, agent_id=agent.id)
        return {"state": TaskState.SUCCEEDED.value}
