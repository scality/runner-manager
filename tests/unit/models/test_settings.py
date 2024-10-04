import os
import tempfile

import pytest
import yaml
from githubkit import AppInstallationAuthStrategy, TokenAuthStrategy
from hypothesis import assume, given
from hypothesis import strategies as st
from pydantic import ConfigError
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
        "runner_groups": [
            {
                "name": "test",
                "backend": {
                    "name": "base",
                    "config": {},
                    "instance_config": {},
                },
                "organization": "octo-org",
                "labels": ["label"],
            },
            {
                "name": "test-openstack",
                "backend": {
                    "name": "openstack",
                    "config": {
                        "cloud": "test-cloud-01",
                        "region_name": "test-region-01",
                    },
                    "instance_config": {},
                },
                "organization": "octo-org",
                "labels": ["label"],
            },
        ],
    }


@fixture(scope="function")
def config_file(yaml_data, monkeypatch):
    # create a yaml file with some data
    with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
        yaml.dump(yaml_data, f)
        monkeypatch.setenv("CONFIG_FILE", f.name)
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


def test_redhat_credentials(config_file, monkeypatch):
    monkeypatch.setenv("REDHAT_USERNAME", "username")
    monkeypatch.setenv("REDHAT_PASSWORD", "password")
    settings = Settings()
    assert (
        settings.runner_groups[0].backend.instance_config.redhat_username == "username"
    )
    assert (
        settings.runner_groups[0].backend.instance_config.redhat_password == "password"
    )


def test_openstack_credentials_yaml(config_file, yaml_data):
    settings = Settings()
    assert (
        settings.runner_groups[1].backend.config.cloud
        == yaml_data["runner_groups"][1]["backend"]["config"]["cloud"]
    )
    assert (
        settings.runner_groups[1].backend.config.region_name
        == yaml_data["runner_groups"][1]["backend"]["config"]["region_name"]
    )


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


@given(
    st.builds(
        Settings,
        github_app_id=st.integers(),
        github_installation_id=st.integers(),
        github_private_key=st.text(),
        github_token=st.text(),
    )
)
def test_app_install(stsettings):
    assume(stsettings.github_app_id)
    assume(stsettings.github_installation_id)
    assume(stsettings.github_private_key)
    assert stsettings.app_install is True
    assert isinstance(stsettings.github_auth_strategy(), AppInstallationAuthStrategy)


@given(
    st.builds(
        Settings,
        github_app_id=st.just(0),
        github_installation_id=st.just(0),
        github_private_key=st.just(""),
    )
)
def test_token_auth_strategy(stsettings):
    if stsettings.github_token:
        assert isinstance(stsettings.github_auth_strategy(), TokenAuthStrategy)


@given(
    st.builds(
        Settings,
        github_token=st.none(),
        github_app_id=st.just(0),
        github_installation_id=st.just(0),
        github_private_key=st.just(""),
    )
)
def test_config_error(stsettings):
    with pytest.raises(ConfigError):
        stsettings.github_auth_strategy()


def test_settings_runner_group(runner_group: RunnerGroup):
    settings = Settings(runner_groups=[runner_group])
    assert settings.runner_groups == [runner_group]
