import os
import tempfile
from pytest import fixture
from pathlib import Path
from runner_manager.models.settings import Settings
from runner_manager.models.settings import yaml_config_settings_source
from runner_manager.models.settings import ConfigFile

@fixture
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
    config_file = ConfigFile(config_file=Path(temp_yaml_file))
    settings = Settings()
    settings.__config__.config = config_file
    config_data = yaml_config_settings_source(settings)
    assert config_data["name"] == "test-runner-manager"
    assert config_data["redis_om_url"] == "redis://localhost:6379/0"
    assert config_data["github_base_url"] == "https://github.com"

def test_env_file():
    os.environ["REDIS_OM_URL"] = "redis://localhost:6379/0"
    os.environ["GITHUB_BASE_URL"] = "https://github.com"
    os.environ["NAME"] = "test-runner-manager"
    settings = Settings()
    assert settings.name == "test-runner-manager"
    assert settings.redis_om_url == os.getenv("REDIS_OM_URL")
    assert settings.github_base_url == os.getenv("GITHUB_BASE_URL")
