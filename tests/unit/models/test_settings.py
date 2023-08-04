import os
import tempfile

import yaml
from pytest import fixture

from runner_manager.models.settings import Settings


def test_settings_default_values():
    settings = Settings()
    assert settings.name == "runner-manager"
    assert settings.redis_om_url == os.getenv("REDIS_OM_URL")
    assert settings.github_base_url == os.getenv("GITHUB_BASE_URL")


@fixture
def temp_yaml_file():
    yaml_data = """
    name: test-runner-manager
    redis_om_url: redis://localhost:6379/0
    github_base_url: https://github.com
    """
    yaml_file = tempfile.NamedTemporaryFile(mode="w", delete=False)
    yaml_file.write(yaml_data)
    return yaml_file.name


def test_yaml_config(temp_yaml_file):
    os.environ["CONFIG_FILE"] = temp_yaml_file
    # settings should automatically look for the config file
    # environment variable and load the file if it exists
    settings = Settings()
    with open(temp_yaml_file) as f:
        yaml_data = yaml.safe_load(f)
    assert settings.name == yaml_data["name"]
    assert settings.redis_om_url == yaml_data["redis_om_url"]
    assert settings.github_base_url == yaml_data["github_base_url"]


def test_env_file():
    os.environ["REDIS_OM_URL"] = "redis://localhost:6379/0"
    os.environ["GITHUB_BASE_URL"] = "https://github.com"
    os.environ["NAME"] = "test-runner-manager"
    settings = Settings()
    assert settings.name == os.getenv("NAME")
    assert settings.redis_om_url == os.getenv("REDIS_OM_URL")
    assert settings.github_base_url == os.getenv("GITHUB_BASE_URL")
