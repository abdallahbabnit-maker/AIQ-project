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
        candidates = [a for a in self.registry.all()
                      if required_skills.issubset(a.skills)]
        if not candidates:
            return None
        return max(candidates, key=lambda a: len(a.skills))

    async def _set_state(self, task_id, state):
        if self.task_repo is not None and hasattr(self.task_repo, "update_state"):
            await self.task_repo.update_state(task_id, state)

    async def submit(self, task):
        task_id = task["id"]
        await self.audit.log("task.queued", task_id=task_id)
        await self._set_state(task_id, TaskState.QUEUED.value)
        required = set(task.get("required_skills", []))
        agent = self.select_agent(required)
        if agent is None:
            await self.audit.log("task.failed", task_id=task_id,
                                 detail={"error": "no_agent_available"})
            await self._set_state(task_id, TaskState.FAILED.value)
            return {"state": TaskState.FAILED.value, "error": "no_agent_available"}
        await self.audit.log("task.assigned", task_id=task_id, agent_id=agent.id)
        await self._set_state(task_id, TaskState.ASSIGNED.value)
        return await self.execute(task, agent, runner=task.get("runner"))

    async def execute(self, task, agent, runner=None):
        task_id = task["id"]
        await self.audit.log("task.started", task_id=task_id, agent_id=agent.id)
        action = task.get("action", "")
        if action not in agent.allowed_actions:
            await self.audit.log("task.blocked_permission", task_id=task_id,
                                 agent_id=agent.id, detail={"action": action})
            await self._set_state(task_id, TaskState.FAILED.value)
            return {"state": TaskState.FAILED.value, "error": "action_not_allowed"}
        from app.orchestrator.approval_gate import RiskLevel
        risk = RiskLevel(task.get("risk", "low"))
        gate_result = await self.gate.request(
            task_id=task_id, agent_id=agent.id, action=action, risk=risk,
            payload=task.get("payload", {}), requested_by=agent.id,
        )
        if not gate_result["approved"]:
            await self.audit.log("task.awaiting_approval", task_id=task_id,
                                 agent_id=agent.id,
                                 detail={"approval_id": gate_result["approval_id"]})
            await self._set_state(task_id, TaskState.AWAITING_APPROVAL.value)
            return {"state": TaskState.AWAITING_APPROVAL.value,
                    "approval_id": gate_result["approval_id"]}
        if runner is None:
            await self.audit.log("task.succeeded", task_id=task_id, agent_id=agent.id)
            await self._set_state(task_id, TaskState.SUCCEEDED.value)
            return {"state": TaskState.SUCCEEDED.value}
        return await self._run_with_retries(task, agent, runner)

    async def _run_with_retries(self, task, agent, runner):
        task_id = task["id"]
        max_attempts = max(1, agent.max_retries + 1)
        last_error = None
        for attempt in range(1, max_attempts + 1):
            await self.audit.log("task.running", task_id=task_id, agent_id=agent.id,
                                 detail={"attempt": attempt})
            await self._set_state(task_id, TaskState.RUNNING.value)
            try:
                result = await runner(task)
            except Exception as exc:
                last_error = str(exc)
                if attempt < max_attempts:
                    await self.audit.log("task.retrying", task_id=task_id,
                                         agent_id=agent.id,
                                         detail={"attempt": attempt, "error": last_error})
                    continue
                await self.audit.log("task.failed", task_id=task_id, agent_id=agent.id,
                                     detail={"error": last_error, "attempts": attempt})
                await self._set_state(task_id, TaskState.FAILED.value)
                return {"state": TaskState.FAILED.value, "error": last_error}
            await self.audit.log("task.succeeded", task_id=task_id, agent_id=agent.id,
                                 detail={"attempt": attempt})
            await self._set_state(task_id, TaskState.SUCCEEDED.value)
            return {"state": TaskState.SUCCEEDED.value, "result": result}
        return {"state": TaskState.FAILED.value, "error": last_error}
