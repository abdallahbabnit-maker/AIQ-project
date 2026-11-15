import os
import pytest
from app.db.health import check_database

@pytest.mark.asyncio
async def test_sqlite_connection():
    result = await check_database()
    assert result["status"] == "ok"
    assert result["probe"] == 1

@pytest.mark.asyncio
@pytest.mark.skipif(not os.getenv("TEST_DATABASE_URL"),
                    reason="TEST_DATABASE_URL not set — real PostgreSQL test skipped")
async def test_postgres_connection_real(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", os.environ["TEST_DATABASE_URL"])
    import importlib
    from app.db import session as session_module, health as health_module
    importlib.reload(session_module)
    importlib.reload(health_module)
    result = await health_module.check_database()
    assert result["status"] == "ok"
    assert result["probe"] == 1
    assert "postgresql" in result["database"]
