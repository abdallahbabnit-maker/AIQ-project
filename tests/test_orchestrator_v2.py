import asyncio

from app.orchestrator.registry import Agent, AgentRegistry
from app.orchestrator.approval_gate import ApprovalGate
from app.orchestrator.engine import Orchestrator, TaskState


class FakeAudit:
    def __init__(self):
        self.events = []

    async def log(self, event_type, task_id=None, agent_id=None, detail=None):
        self.events.append((event_type, task_id, agent_id, detail))


class FakeApprovalRepo:
    def __init__(self):
        self.items = []

    async def create(self, approval):
        self.items.append(approval)


class FakeTaskRepo:
    def __init__(self):
        self.states = []

    async def update_state(self, task_id, state):
        self.states.append((task_id, state))


def make_orchestrator(agents=None, task_repo=None):
    audit = FakeAudit()
    gate = ApprovalGate(FakeApprovalRepo(), audit)
    reg = AgentRegistry(agents or [])
    return Orchestrator(reg, gate, audit, task_repo=task_repo), audit


def make_agent(**kw):
    base = dict(id="a1", name="Agent One",
                skills={"research", "writing"},
                allowed_actions={"research_topic", "publish_content"},
                max_retries=2)
    base.update(kw)
    return Agent(**base)


def run(coro):
    return asyncio.run(coro)


def test_retry_then_success():
    orch, audit = make_orchestrator([make_agent()])
    calls = {"n": 0}

    async def runner(task):
        calls["n"] += 1
        if calls["n"] < 3:
            raise RuntimeError("boom")
        return {"ok": True}

    task = {"id": "t1", "action": "research_topic", "risk": "low"}
    result = run(orch.execute(task, orch.registry.get("a1"), runner=runner))
    assert result["state"] == TaskState.SUCCEEDED.value
    assert calls["n"] == 3
    retries = [e for e in audit.events if e[0] == "task.retrying"]
    assert len(retries) == 2


def test_retry_limit_exhausted_fails():
    orch, audit = make_orchestrator([make_agent(max_retries=1)])

    async def runner(task):
        raise RuntimeError("always")

    task = {"id": "t2", "action": "research_topic", "risk": "low"}
    result = run(orch.execute(task, orch.registry.get("a1"), runner=runner))
    assert result["state"] == TaskState.FAILED.value
    running = [e for e in audit.events if e[0] == "task.running"]
    assert len(running) == 2
    assert any(e[0] == "task.failed" for e in audit.events)


def test_states_persisted():
    repo = FakeTaskRepo()
    orch, audit = make_orchestrator([make_agent()], task_repo=repo)

    async def runner(task):
        return 42

    task = {"id": "t3", "action": "research_topic", "risk": "low"}
    run(orch.execute(task, orch.registry.get("a1"), runner=runner))
    states = [s for _, s in repo.states]
    assert TaskState.RUNNING.value in states
    assert states[-1] == TaskState.SUCCEEDED.value


def test_submit_selects_by_skills():
    a1 = make_agent(id="a1", skills={"research"})
    a2 = make_agent(id="a2", skills={"research", "writing"})
    orch, audit = make_orchestrator([a1, a2])
    task = {"id": "t4", "action": "research_topic", "risk": "low",
            "required_skills": ["research", "writing"]}
    result = run(orch.submit(task))
    assert result["state"] == TaskState.SUCCEEDED.value
    assigned = [e for e in audit.events if e[0] == "task.assigned"]
    assert assigned[0][2] == "a2"


def test_submit_no_agent_fails():
    orch, audit = make_orchestrator([make_agent(skills={"research"})])
    task = {"id": "t5", "action": "research_topic", "risk": "low",
            "required_skills": ["video_editing"]}
    result = run(orch.submit(task))
    assert result["state"] == TaskState.FAILED.value
    assert result["error"] == "no_agent_available"


def test_sensitive_still_blocked_with_runner():
    orch, audit = make_orchestrator([make_agent()])

    async def runner(task):
        raise AssertionError("must not run")

    task = {"id": "t6", "action": "publish_content", "risk": "low"}
    result = run(orch.execute(task, orch.registry.get("a1"), runner=runner))
    assert result["state"] == TaskState.AWAITING_APPROVAL.value
