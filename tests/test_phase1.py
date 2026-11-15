import asyncio
import uuid

import pytest
from sqlalchemy import text, inspect
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.db.base import Base
import app.models  # noqa: F401
from app.models import Skill


def _is_pg():
    return settings.DATABASE_URL.startswith("postgresql")


async def _pg_select1():
    engine = create_async_engine(settings.DATABASE_URL)
    try:
        async with engine.connect() as conn:
            return (await conn.execute(text("SELECT 1"))).scalar()
    finally:
        await engine.dispose()


def test_postgres_connection():
    if not _is_pg():
        pytest.skip("DATABASE_URL is not PostgreSQL")
    assert asyncio.run(_pg_select1()) == 1


async def _pg_tables():
    engine = create_async_engine(settings.DATABASE_URL)
    try:
        async with engine.connect() as conn:
            return await conn.run_sync(
                lambda c: inspect(c).get_table_names()
            )
    finally:
        await engine.dispose()


def test_migration_tables_exist():
    if not _is_pg():
        pytest.skip("DATABASE_URL is not PostgreSQL")
    tables = asyncio.run(_pg_tables())
    for t in ["agents", "skills", "tasks", "approvals",
              "audit_events", "alembic_version"]:
        assert t in tables, f"missing table: {t}"


async def _sqlite_crud():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    Session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with Session() as s:
        sk = Skill(name="skill-" + uuid.uuid4().hex[:8])
        s.add(sk)
        await s.commit()
        await s.refresh(sk)
        ok = sk.id is not None and len(sk.id) == 36
    await engine.dispose()
    return ok


def test_sqlite_still_works_for_tests():
    assert asyncio.run(_sqlite_crud())
