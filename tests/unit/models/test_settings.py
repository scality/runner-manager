from runner_manager.models.settings import Settings
from pytest import fixture


def test_settings_default_values():
    settings = Settings()
    assert settings.name == "runner-manager"
    assert settings.redis_om_url == "redis://localhost:6379/0"
    assert settings.github_base_url == "http://localhost:4010"

@fixture
def test_env_settings():
    env_settings = {
        "NAME": "name-test",
        "REDIS_OM_URL": "redis://localhost:6379/1",
        "GITHUB_BASE_URL": "http://localhost:4999",
    }
    settings = Settings()
    settings.Config.customise_sources(env_settings=env_settings, init_settings={}, file_secret_settings={})
    assert settings.name == "name-test"
    assert settings.redis_om_url == "redis://localhost:6379/1"
    assert settings.github_base_url == "http://localhost:4999"