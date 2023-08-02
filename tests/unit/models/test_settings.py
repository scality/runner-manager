from runner_manager.models.settings import Settings
from pydantic import AnyHttpUrl, RedisDsn


def test_settings_default_values():
    settings = Settings()
    assert settings.name == "runner-manager"
    assert settings.redis_om_url is None
    assert settings.github_base_url is None



def test_settings_override_values():
    redis_url = RedisDsn.build(scheme="redis", host="localhost", port="6379")
    github_url = AnyHttpUrl.build(scheme="https", host="github.com", port="443")
    settings = Settings(name="test", redis_om_url=redis_url, github_base_url=github_url)
    assert settings.name == "test"
    assert settings.redis_om_url == redis_url
    assert settings.github_base_url == github_url


