import os
import tempfile

import pytest
import yaml
from pytest import fixture

from runner_manager.dependencies import get_settings
from runner_manager.models.runner_group import RunnerGroup
from runner_manager.models.settings import ConfigFile, Settings


@fixture
def yaml_data():
    return {
        "name": "test-runner-manager",
        "redis_om_url": "redis://localhost:6379/0",
        "github_base_url": "https://github.com",
    }


@fixture(scope="function")
def config_file(yaml_data):
    # create a yaml file with some data
    with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
        yaml.dump(yaml_data, f)
        os.environ["CONFIG_FILE"] = f.name
        config = ConfigFile()
        return config.config_file


def test_settings_default_values():
    settings = Settings()
    assert settings.name == "runner-manager"
    assert settings.redis_om_url == os.getenv("REDIS_OM_URL")
    assert settings.github_base_url == os.getenv("GITHUB_BASE_URL")


def test_invalid_redis_url():
    with pytest.raises(ValueError):
        Settings(redis_om_url="invalid_redis_url")


def test_invalid_github_url():
    with pytest.raises(ValueError):
        Settings(github_base_url="invalid_github_url")


def test_yaml_config(config_file, yaml_data):
    settings = Settings()
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


def test_get_settings(config_file):
    get_settings()
    # delete config_file
    os.remove(config_file)
    # call settings again to ensure the cached settings are returned
    get_settings()
    with pytest.raises(FileNotFoundError):
        Settings()


def test_settings_runner_group(runner_group: RunnerGroup):
    settings = Settings(runner_groups=[runner_group])
    assert settings.runner_groups == [runner_group]