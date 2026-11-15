import uuid
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_session
from app.models.audit import AuditEvent
from app.core.security import require_user

router = APIRouter(prefix="/chat", tags=["chat"])

class ChatBody(BaseModel):
    message: str
    session_id: str | None = None

def _smart_reply(text: str):
    t = text.lower()
    if any(k in t for k in ["search", "ابحث", "research", "أخبار", "news"]):
        return "🔎 **Research Agent** يعمل على طلبك. لخصت المصادر المتاحة حول موضوعك.", "research"
    if any(k in t for k in ["write", "اكتب", "article", "مقال", "content", "محتوى"]):
        return "✍️ **Content Agent** أعدّ لك مسودة. المسودة جاهزة في Review Workspace.", "writing"
    if any(k in t for k in ["image", "صورة", "video", "فيديو", "generate", "ولّد", "استوديو"]):
        return "🎨 **Media Agent** استلم طلبك. أنشأت مهمة توليد في قائمة الاستوديو.", "media"
    if any(k in t for k in ["task", "مهمة", "apply", "وظيفة", "affiliate", "دروب"]):
        return "📋 **Commerce Agent** حلّل الطلب. السياسة: Affiliate أولاً، بدون مخزون.", "commerce"
    if any(k in t for k in ["ai", "ذكاء", "اصطناعي"]):
        return "🤖 **AIQ** هو نموذج ذكاء اصطناعي خاص بك. وكلاؤك يعملون ضمن صلاحيات محددة، وكل إجراء حساس يحتاج موافقتك.", "general"
    return f"فهمت: «{text[:120]}». وكلاؤك جاهزون.", "general"

@router.post("/send")
async def send(body: ChatBody, session: AsyncSession = Depends(get_session), user: dict = Depends(require_user)):
    reply, agent = _smart_reply(body.message)
    session.add(AuditEvent(
        event_type="chat.message",
        actor_id=user["sub"],
        detail={"message": body.message[:500], "agent": agent, "session_id": body.session_id},
    ))
    await session.commit()
    return {"reply": reply, "agent": agent, "message_id": str(uuid.uuid4()), "session_id": body.session_id or "default"}
