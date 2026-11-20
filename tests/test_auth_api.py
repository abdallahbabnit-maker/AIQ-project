import asyncio

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from app.db.base import Base
import app.models  # noqa: F401
from app.models import Task, Approval, User
from app.db.session import get_session
from app.main import app
from app.core.security import hash_password, verify_password, create_token

FOUNDER_PW = "founder-pass-123"
REVIEWER_PW = "reviewer-pass-123"
AGENT_PW = "agent-pass-123"


@pytest.fixture()
def client(tmp_path):
    engine = create_async_engine(f"sqlite+aiosqlite:///{tmp_path}/auth.db")
    Session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async def init():
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        async with Session() as s:
            s.add(User(username="boss", password_hash=hash_password(FOUNDER_PW), role="founder"))
            s.add(User(username="rev", password_hash=hash_password(REVIEWER_PW), role="reviewer"))
            s.add(User(username="bot", password_hash=hash_password(AGENT_PW), role="agent"))
            t = Task(title="T", action="publish_content", payload={"x": 1}, risk="high")
            s.add(t)
            await s.flush()
            s.add(Approval(task_id=t.id, agent_id="a1", action="publish_content",
                           risk="high", payload={"x": 1}, status="pending",
                           requested_by="a1"))
            await s.commit()
    asyncio.run(init())

    async def override():
        async with Session() as s:
            yield s

    app.dependency_overrides[get_session] = override
    with TestClient(app) as c:
        yield c, Session
    app.dependency_overrides.clear()
    asyncio.run(engine.dispose())


def login(c, u, p):
    return c.post("/auth/login", json={"username": u, "password": p})


def auth(token):
    return {"Authorization": "Bearer " + token}


def approval_id(Session):
    async def _q():
        async with Session() as s:
            return (await s.execute(select(Approval))).scalars().first().id
    return asyncio.run(_q())


def test_login_success(client):
    c, S = client
    r = login(c, "boss", FOUNDER_PW)
    assert r.status_code == 200
    assert r.json()["role"] == "founder"
    assert r.json()["access_token"]


def test_login_wrong_password_401(client):
    c, S = client
    assert login(c, "boss", "wrong-password").status_code == 401


def test_login_unknown_user_401(client):
    c, S = client
    assert login(c, "ghost", "whatever-123").status_code == 401


def test_review_without_token_401(client):
    c, S = client
    assert c.get("/review/pending").status_code == 401


def test_review_with_valid_token_200(client):
    c, S = client
    token = login(c, "boss", FOUNDER_PW).json()["access_token"]
    assert c.get("/review/pending", headers=auth(token)).status_code == 200


def test_garbage_token_401(client):
    c, S = client
    assert c.get("/review/pending", headers=auth("abc.def")).status_code == 401


def test_tampered_token_401(client):
    c, S = client
    t = login(c, "boss", FOUNDER_PW).json()["access_token"]
    bad = t[:-1] + ("0" if t[-1] != "0" else "1")
    assert c.get("/review/pending", headers=auth(bad)).status_code == 401


def test_expired_token_401(client):
    c, S = client
    t = create_token("u1", "founder", ttl_seconds=-10)
    assert c.get("/review/pending", headers=auth(t)).status_code == 401


def test_agent_role_cannot_decide_403(client):
    c, S = client
    aid = approval_id(S)
    t = login(c, "bot", AGENT_PW).json()["access_token"]
    r = c.post(f"/review/{aid}/decide", headers=auth(t),
               json={"decision": "approve", "reviewer_id": "bot"})
    assert r.status_code == 403


def test_reviewer_can_decide_200(client):
    c, S = client
    aid = approval_id(S)
    t = login(c, "rev", REVIEWER_PW).json()["access_token"]
    r = c.post(f"/review/{aid}/decide", headers=auth(t),
               json={"decision": "approve", "reviewer_id": "rev"})
    assert r.status_code == 200



def test_reviewer_identity_comes_from_token_not_request_body(client):
    c, S = client
    aid = approval_id(S)
    t = login(c, "rev", REVIEWER_PW).json()["access_token"]
    r = c.post(
        f"/review/{aid}/decide",
        headers=auth(t),
        json={
            "decision": "approve",
            "reviewer_id": "forged-founder-id",
            "note": "identity must be token-derived",
        },
    )
    assert r.status_code == 200

    async def _q():
        async with S() as s:
            approval = await s.get(Approval, aid)
            return approval.decided_by

    assert asyncio.run(_q()) == "rev"


def test_password_stored_hashed(client):
    c, S = client

    async def _q():
        async with S() as s:
            u = (await s.execute(select(User).where(User.username == "boss"))).scalars().first()
            return u.password_hash
    stored = asyncio.run(_q())
    assert stored != FOUNDER_PW
    assert "$" in stored
    assert verify_password(FOUNDER_PW, stored)
