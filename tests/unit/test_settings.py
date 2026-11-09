import pytest

from automation_architect.config.settings import Settings


def test_reads_values_from_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("APP_ENV", "test")
    monkeypatch.setenv("N8N_BASE_URL", "http://localhost:5678")
    monkeypatch.setenv("N8N_API_KEY", "n8n-secret")

    settings = Settings(_env_file=None)

    assert settings.app_env == "test"
    assert str(settings.n8n_base_url) == "http://localhost:5678/"
    assert settings.n8n_api_key is not None
    assert settings.n8n_api_key.get_secret_value() == "n8n-secret"


def test_secrets_are_not_exposed_in_repr(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-secret")
    monkeypatch.setenv("N8N_API_KEY", "n8n-secret")

    rendered = repr(Settings(_env_file=None))

    assert "sk-ant-secret" not in rendered
    assert "n8n-secret" not in rendered
