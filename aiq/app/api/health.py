from fastapi import APIRouter
from app.db.health import check_database

router = APIRouter(prefix="/health", tags=["health"])

@router.get("")
async def health():
    return {"status": "ok"}

@router.get("/db")
async def db_health():
    return await check_database()
