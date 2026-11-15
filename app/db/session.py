from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool
from app.core.config import settings

def _build_engine(url: str):
    kwargs: dict = {"echo": settings.SQL_ECHO, "future": True}
    if url.startswith("sqlite"):
        kwargs["connect_args"] = {"check_same_thread": False}
        if ":memory:" in url:
            kwargs["poolclass"] = StaticPool
    else:
        kwargs.update(pool_size=5, max_overflow=10, pool_pre_ping=True)
    return create_async_engine(url, **kwargs)

engine = _build_engine(settings.DATABASE_URL)
SessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def get_session():
    async with SessionLocal() as session:
        yield session
