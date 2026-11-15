from sqlalchemy import text
from app.db.session import engine

async def check_database() -> dict:
    safe_url = engine.url.render_as_string(hide_password=True)
    try:
        async with engine.connect() as conn:
            result = await conn.execute(text("SELECT 1"))
            probe = result.scalar_one()
        return {"status": "ok", "database": safe_url, "probe": probe}
    except Exception as exc:
        return {"status": "error", "database": safe_url, "error": repr(exc)}
