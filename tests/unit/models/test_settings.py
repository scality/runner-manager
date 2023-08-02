from runner_manager.models.settings import Settings
from runner_manager.models.settings import yaml_config_settings_source
from pytest import fixture
import tempfile
import os
import yaml
from pathlib import Path

@fixture
def temp_yaml_file():
    settings_data = {
        "name": "runner-test",
        "redis_om_url": "redis://localhost:6379/0",
        "github_base_url": "https://www.github.com"
    }

    with tempfile.NamedTemporaryFile(mode="w", delete=False) as temp_file:
        yaml.dump(settings_data, temp_file)
        temp_file.flush()
        yield temp_file.name

    # Clean up the temporary file after the test is finished
    os.remove(temp_file.name)

@fixture
def temp_env_file():
    env_data = [
        "NAME=runner-test",
        "REDIS_OM_URL=redis://env-localhost:6379/0",
        "GITHUB_BASE_URL=https://www.github.com"
    ]

    with tempfile.NamedTemporaryFile(mode="w", delete=False) as temp_file:
        temp_file.write("\n".join(env_data))
        temp_file.flush()
        yield temp_file.name

    # Clean up the temporary file after the test is finished
    os.remove(temp_file.name)

@fixture
def test_settings_default_values():
    settings = Settings()
    assert settings.name == "runner-manager"
    assert settings.redis_om_url is None
    assert settings.github_base_url is None

@fixture
def test_yaml_config_settings(temp_yaml_file):
    settings = Settings()
    settings.__config__.config.config_file = Path(temp_yaml_file)
    custom_settings = yaml_config_settings_source(settings)
    assert custom_settings["name"] == "runner-test"
    assert custom_settings["redis_om_url"] == "redis://localhost:6379/0"
    assert custom_settings["github_base_url"] == "https://www.github.com"

