from runner_manager.models.settings import Settings
from pydantic import AnyHttpUrl, RedisDsn


def test_settings_default_values():
    settings = Settings()
    assert settings.name == "runner-manager"
    assert settings.redis_om_url is None
    assert settings.github_base_url is None




