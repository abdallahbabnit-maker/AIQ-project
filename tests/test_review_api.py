import asyncio

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from app.db.base import Base
import app.models  # noqa: F401
from app.models import Task, Approval, AuditEvent
from app.db.session import get_session
from app.main import app
from app.core.security import require_user, require_reviewer


@pytest.fixture()
def client(tmp_path):
    engine = create_async_engine(f"sqlite+aiosqlite:///{tmp_path}/review.db")
    Session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async def init():
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    asyncio.run(init())

    async def override():
        async with Session() as s:
            yield s

    app.dependency_overrides[get_session] = override
    app.dependency_overrides[require_user] = lambda: {"sub": "founder-1", "role": "founder"}
    app.dependency_overrides[require_reviewer] = lambda: {"sub": "founder-1", "role": "founder"}
    with TestClient(app) as c:
        yield c, Session
    app.dependency_overrides.clear()
    asyncio.run(engine.dispose())


def seed(Session):
    async def _seed():
        async with Session() as s:
            t = Task(title="Publish article", action="publish_content",
                     payload={"content": "hello world"}, risk="high")
            s.add(t)
            await s.flush()
            a = Approval(task_id=t.id, agent_id="agent-1",
                         action="publish_content", risk="high",
                         payload={"content": "hello world"},
                         status="pending", requested_by="agent-1")
            s.add(a)
            await s.commit()
            return t.id, a.id
    return asyncio.run(_seed())


def test_pending_lists_output(client):
    c, Session = client
    tid, aid = seed(Session)
    r = c.get("/review/pending")
    assert r.status_code == 200
    items = r.json()
    assert any(i["approval_id"] == aid for i in items)
    assert items[0]["payload"]["content"] == "hello world"


def test_approve_runs_task_and_audits(client):
    c, Session = client
    tid, aid = seed(Session)
    r = c.post(f"/review/{aid}/decide",
               json={"decision": "approve", "reviewer_id": "founder", "note": "ok"})
    assert r.status_code == 200
    assert r.json()["status"] == "approved"
    r2 = c.get(f"/review/task/{tid}")
    assert r2.json()["state"] == "running"

    async def check():
        async with Session() as s:
            rows = (await s.execute(select(AuditEvent).where(
                AuditEvent.event_type == "review.approve"))).scalars().all()
            return len(rows)
    assert asyncio.run(check()) == 1


def test_reject_cancels_task(client):
    c, Session = client
    tid, aid = seed(Session)
    r = c.post(f"/review/{aid}/decide",
               json={"decision": "reject", "reviewer_id": "founder"})
    assert r.status_code == 200
    assert c.get(f"/review/task/{tid}").json()["state"] == "cancelled"


def test_request_changes(client):
    c, Session = client
    tid, aid = seed(Session)
    r = c.post(f"/review/{aid}/decide",
               json={"decision": "request_changes", "reviewer_id": "founder",
                     "note": "fix title"})
    assert r.status_code == 200
    assert r.json()["status"] == "changes_requested"


def test_double_decide_409(client):
    c, Session = client
    tid, aid = seed(Session)
    body = {"decision": "approve", "reviewer_id": "founder"}
    assert c.post(f"/review/{aid}/decide", json=body).status_code == 200
    assert c.post(f"/review/{aid}/decide", json=body).status_code == 409


def test_unknown_404(client):
    c, Session = client
    r = c.post("/review/nope/decide",
               json={"decision": "approve", "reviewer_id": "founder"})
    assert r.status_code == 404


def test_invalid_decision_422(client):
    c, Session = client
    tid, aid = seed(Session)
    r = c.post(f"/review/{aid}/decide",
               json={"decision": "delete_all", "reviewer_id": "founder"})
    assert r.status_code == 422


def test_history_shows_decided(client):
    c, Session = client
    tid, aid = seed(Session)
    c.post(f"/review/{aid}/decide",
           json={"decision": "approve", "reviewer_id": "founder"})
    r = c.get("/review/history")
    assert r.status_code == 200
    assert any(i["approval_id"] == aid for i in r.json())
