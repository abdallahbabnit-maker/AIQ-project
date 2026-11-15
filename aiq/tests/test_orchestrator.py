import pytest
from app.orchestrator.engine import Orchestrator, TaskState
from app.orchestrator.registry import Agent, AgentRegistry
from app.orchestrator.approval_gate import ApprovalGate

class FakeRepo:
    async def create(self, row): pass

class FakeAudit:
    async def log(self, *a, **kw): pass

@pytest.mark.asyncio
async def test_agent_cannot_execute_action_outside_permissions():
    registry = AgentRegistry([Agent(id="a1", name="A1", skills={"write"}, allowed_actions={"read_data"})])
    orch = Orchestrator(registry, ApprovalGate(FakeRepo(), FakeAudit()), FakeAudit())
    task = {"id": "t1", "action": "publish_content", "required_skills": ["write"], "risk": "low"}
    result = await orch.execute(task, registry.get("a1"))
    assert result["state"] == TaskState.FAILED.value
    assert result["error"] == "action_not_allowed"

@pytest.mark.asyncio
async def test_sensitive_task_stops_at_approval_gate():
    registry = AgentRegistry([Agent(id="a1", name="A1", skills={"write"}, allowed_actions={"publish_content"})])
    orch = Orchestrator(registry, ApprovalGate(FakeRepo(), FakeAudit()), FakeAudit())
    task = {"id": "t1", "action": "publish_content", "required_skills": ["write"], "risk": "high"}
    result = await orch.execute(task, registry.get("a1"))
    assert result["state"] == TaskState.AWAITING_APPROVAL.value
    assert result["approval_id"]
