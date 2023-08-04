from pathlib import Path
from typing import Any, Dict, Optional

import yaml
from pydantic import AnyHttpUrl, BaseSettings, RedisDsn, SecretStr


def yaml_config_settings_source(settings: BaseSettings) -> Dict[str, Any]:
    """
    A simple settings source that loads variables from a yaml file

    """
    config_file: Optional[Path] = settings.__config__.config.config_file
    if config_file:
        return yaml.full_load(config_file.read_text())
    return {}


class ConfigFile(BaseSettings):
    config_file: Optional[Path] = None


class Settings(BaseSettings):
    name: str = "runner-manager"
    redis_om_url: Optional[RedisDsn] = None
    github_base_url: Optional[AnyHttpUrl] = None
    API_KEY: Optional[SecretStr] = None

    class Config:
        config: ConfigFile = ConfigFile()
        env_file = ".env"
        env_file_encoding = "utf-8"

        @classmethod
        def customise_sources(
            cls,
            init_settings,
            env_settings,
            file_secret_settings,
        ):
            return (
                init_settings,
                yaml_config_settings_source,
                env_settings,
                file_secret_settings,
            )
