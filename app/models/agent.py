import uuid
from datetime import datetime, timezone
from sqlalchemy import String, DateTime, JSON, Boolean
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base

class Agent(Base):
    __tablename__ = "agents"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String(120), unique=True, index=True)
    skills: Mapped[list] = mapped_column(JSON, default=list)
    allowed_actions: Mapped[list] = mapped_column(JSON, default=list)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
