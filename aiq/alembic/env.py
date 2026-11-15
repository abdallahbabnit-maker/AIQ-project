from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context

from app.core.config import settings
from app.db.base import Base
import app.models  # noqa: F401

config = context.config
target_metadata = Base.metadata

def _sync_url(url: str) -> str:
    return url.replace("+asyncpg", "").replace("+aiosqlite", "")

def run_migrations_offline() -> None:
    context.configure(
        url=_sync_url(settings.DATABASE_URL),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online() -> None:
    section = config.get_section(config.config_ini_section, {})
    section["sqlalchemy.url"] = _sync_url(settings.DATABASE_URL)
    connectable = engine_from_config(section, prefix="sqlalchemy.", poolclass=pool.NullPool)
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
