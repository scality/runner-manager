from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

import yaml
from githubkit import AppInstallationAuthStrategy, TokenAuthStrategy
from pydantic import AnyHttpUrl, BaseSettings, ConfigError, RedisDsn, SecretStr

from runner_manager.models.runner_group import BaseRunnerGroup


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
    name: str = "runner-manager"
    redis_om_url: Optional[RedisDsn] = None
    api_key: Optional[SecretStr] = None
    allowed_hosts: Optional[Sequence[str]] = [
        "*",
    ]
    log_level: LogLevel = LogLevel.INFO
    runner_groups: List[BaseRunnerGroup] = []

    github_base_url: AnyHttpUrl = AnyHttpUrl("api.github.com", scheme="https")
    github_webhook_secret: Optional[SecretStr] = None
    github_token: Optional[SecretStr] = None
    github_app_id: int | str = 0
    github_private_key: SecretStr = SecretStr("")
    github_installation_id: int = 0
    github_client_id: Optional[str] = None
    github_client_secret: SecretStr = SecretStr("")

    @property
    def app_install(self) -> bool:
        """
        Returns True if the github auth strategy should be an app install.

        To consider an app install user should define:

        - github_app_id
        - github_private_key
        - github_installation_id
        """
        if (
            self.github_app_id
            and self.github_private_key
            and self.github_installation_id
        ):
            return True
        return False

    def github_auth_strategy(self) -> AppInstallationAuthStrategy | TokenAuthStrategy:
        """
        Returns the appropriate auth strategy for the current configuration.
        """
        # prefer AppInstallationAuthStrategy over TokenAuthStrategy
        if self.app_install:
            return AppInstallationAuthStrategy(
                app_id=self.github_app_id,
                installation_id=self.github_installation_id,
                private_key=self.github_private_key.get_secret_value(),
                client_id=self.github_client_id,
                client_secret=self.github_client_secret.get_secret_value(),
            )
        elif self.github_token:
            return TokenAuthStrategy(token=self.github_token.get_secret_value())
        else:
            raise ConfigError("No github auth strategy configured")

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
