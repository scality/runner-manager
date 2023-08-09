from enum import Enum
from pathlib import Path
from typing import Any, Dict, Optional

import yaml
from pydantic import AnyHttpUrl, BaseSettings, RedisDsn, SecretStr


class ConfigFile(BaseSettings):
    config_file: Optional[Path] = None


def yaml_config_settings_source(settings: BaseSettings) -> Dict[str, Any]:
    """
    A simple settings source that loads variables from a yaml file

    """

    config = ConfigFile()
    if config.config_file is not None:
        return yaml.full_load(config.config_file.read_text())
    return {}


class LogLevel(str, Enum):
    INFO = "INFO"
    WARNING = "WARNING"
    DEBUG = "DEBUG"
    ERROR = "ERROR"


class Settings(BaseSettings):
    name: Optional[str] = "runner-manager"
    redis_om_url: Optional[RedisDsn] = None
    github_base_url: Optional[AnyHttpUrl] = None
    github_webhook_secret: Optional[SecretStr] = None
    log_level: LogLevel = LogLevel.INFO

    class Config:
        smart_union = True
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
