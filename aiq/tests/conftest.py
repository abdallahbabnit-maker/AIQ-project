import pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.pool import StaticPool
from app.db.base import Base
import app.models  # noqa

@pytest_asyncio.fixture
async def sqlite_engine():
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()

@pytest_asyncio.fixture
async def sqlite_session(sqlite_engine):
    factory = async_sessionmaker(sqlite_engine, expire_on_commit=False)
    async with factory() as session:
        yield session
