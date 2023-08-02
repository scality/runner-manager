from runner_manager.models.settings import Settings
from runner_manager.models.settings import yaml_config_settings_source
from pytest import fixture
import tempfile
import os
import yaml
from pathlib import Path


@fixture
def test_settings_default_values():
    settings = Settings()
    assert settings.name == "runner-manager"
    assert settings.redis_om_url is None
    assert settings.github_base_url is None