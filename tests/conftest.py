import os
import subprocess
from pathlib import Path

import pytest
from sqlalchemy.orm import Session

from dashboard import db as db_module
from dashboard.config import get_settings


@pytest.fixture
def fresh_db(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    db_file = tmp_path / "test.db"
    db_url = f"sqlite:///{db_file}"
    monkeypatch.setenv("DATABASE_URL", db_url)
    get_settings.cache_clear()
    db_module.reset_engine_cache()

    repo_root = Path(__file__).resolve().parent.parent
    env = os.environ.copy()
    env["DATABASE_URL"] = db_url
    env["PYTHONPATH"] = str(repo_root / "src")
    subprocess.run(
        ["alembic", "-c", str(repo_root / "alembic.ini"), "upgrade", "head"],
        cwd=repo_root,
        env=env,
        check=True,
        capture_output=True,
    )
    return db_file


@pytest.fixture
def session(fresh_db: Path) -> Session:
    SessionLocal = db_module.get_sessionmaker()
    s = SessionLocal()
    try:
        yield s
    finally:
        s.close()
