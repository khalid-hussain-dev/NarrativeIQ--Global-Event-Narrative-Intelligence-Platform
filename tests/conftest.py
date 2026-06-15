import sys
from pathlib import Path
import pytest
from starlette.testclient import TestClient

# Add backend to path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

from app.main import app

@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c
