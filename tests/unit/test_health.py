from fastapi.testclient import TestClient

from automation_architect.bootstrap import create_app
from automation_architect.config.settings import Settings


def test_health_returns_ok() -> None:
    client = TestClient(create_app(Settings(app_env="test")))

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
