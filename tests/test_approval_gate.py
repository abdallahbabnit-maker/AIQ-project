import pytest
from app.orchestrator.approval_gate import ApprovalGate, RiskLevel

class FakeRepo:
    def __init__(self): self.rows = []
    async def create(self, row): self.rows.append(row)

class FakeAudit:
    async def log(self, *a, **kw): pass

def test_high_risk_always_requires_approval():
    gate = ApprovalGate(FakeRepo(), FakeAudit())
    assert gate.requires_approval("read_data", RiskLevel.HIGH) is True
    assert gate.requires_approval("publish_content", RiskLevel.LOW) is True

@pytest.mark.asyncio
async def test_low_risk_non_sensitive_auto_allowed():
    gate = ApprovalGate(FakeRepo(), FakeAudit())
    result = await gate.request(task_id="t1", agent_id="a1", action="read_data",
                                risk=RiskLevel.LOW, payload={}, requested_by="a1")
    assert result["approved"] is True and result["auto"] is True

@pytest.mark.asyncio
async def test_sensitive_action_never_auto_approved():
    gate = ApprovalGate(FakeRepo(), FakeAudit())
    result = await gate.request(task_id="t1", agent_id="a1", action="publish_content",
                                risk=RiskLevel.MEDIUM, payload={}, requested_by="a1")
    assert result["approved"] is False and result["status"] == "pending"
