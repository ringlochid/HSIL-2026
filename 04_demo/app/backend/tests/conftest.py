from __future__ import annotations

from pathlib import Path
import sys

import pytest
from fastapi.testclient import TestClient

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.core.config import Settings
from app.main import create_app


@pytest.fixture()
def app(tmp_path: Path):
    settings = Settings(
        upload_dir=tmp_path / 'uploads',
        database_url=f"sqlite+pysqlite:///{(tmp_path / 'app.db').as_posix()}",
        llm_provider='mock',
        use_real_apis=False,
        max_upload_mb=5,
        debug=True,
    )
    return create_app(settings)


@pytest.fixture()
def client(app):
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture()
def pdf_bytes() -> bytes:
    return b'%PDF-1.4\n1 0 obj<<>>endobj\ntrailer<<>>\n%%EOF\n'
