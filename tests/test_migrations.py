import os, subprocess, sys
from pathlib import Path

def test_migrations_apply_on_sqlite(tmp_path):
    db_file = tmp_path / "migration_test.db"
    env = os.environ.copy()
    env["DATABASE_URL"] = f"sqlite+aiosqlite:///{db_file}"
    result = subprocess.run(
        [sys.executable, "-m", "alembic", "upgrade", "head"],
        cwd=Path(__file__).resolve().parents[1], env=env,
        capture_output=True, text=True,
    )
    assert result.returncode == 0, result.stderr
    assert db_file.exists()
