from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_session
from app.models.user import User
from app.core.security import verify_password, create_token

router = APIRouter(prefix="/auth", tags=["auth"])


class LoginBody(BaseModel):
    username: str
    password: str


@router.post("/login")
async def login(body: LoginBody, session: AsyncSession = Depends(get_session)):
    user = (await session.execute(
        select(User).where(User.username == body.username)
    )).scalars().first()
    if not user or not verify_password(body.password, user.password_hash):
        raise HTTPException(401, "invalid_credentials")
    token = create_token(user.id, user.role)
    return {"access_token": token, "token_type": "bearer", "role": user.role}
