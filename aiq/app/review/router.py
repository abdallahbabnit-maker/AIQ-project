from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_session
from app.models.approval import Approval
from app.models.task import Task
from app.review.schemas import ReviewDecision

router = APIRouter(prefix="/review", tags=["review"])

@router.get("/pending")
async def list_pending(session: AsyncSession = Depends(get_session)):
    rows = (await session.execute(
        select(Approval).where(Approval.status == "pending").order_by(Approval.created_at.desc())
    )).scalars().all()
    return [
        {"approval_id": r.id, "task_id": r.task_id, "agent_id": r.agent_id,
         "action": r.action, "risk": r.risk, "payload": r.payload,
         "created_at": r.created_at.isoformat()}
        for r in rows
    ]

@router.post("/{approval_id}/decide")
async def decide(approval_id: str, body: ReviewDecision,
                 session: AsyncSession = Depends(get_session)):
    approval = await session.get(Approval, approval_id)
    if not approval:
        raise HTTPException(404, "approval_not_found")
    if approval.status != "pending":
        raise HTTPException(409, "approval_already_decided")
    mapping = {"approve": "approved", "reject": "rejected", "request_changes": "changes_requested"}
    approval.status = mapping[body.decision]
    approval.decided_by = body.reviewer_id
    approval.decision_note = body.note
    approval.decided_at = datetime.now(timezone.utc)
    if approval.task_id:
        task = await session.get(Task, approval.task_id)
        if task and body.decision == "approve":
            task.state = "running"
        elif task and body.decision == "reject":
            task.state = "cancelled"
    await session.commit()
    return {"approval_id": approval.id, "status": approval.status}
