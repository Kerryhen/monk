# tests/conftest.py
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.sessions import MonkSession, get_monk_session
from app.settings import Settings

settings = Settings()


@pytest.fixture(scope='session')
def client():
    return TestClient(app)


@pytest.fixture(autouse=True)
def override_monk():
    def fake_monk():
        return MonkSession(username=settings.LISTMONK_USER)

    app.dependency_overrides[get_monk_session] = fake_monk
    yield
    app.dependency_overrides.clear()
