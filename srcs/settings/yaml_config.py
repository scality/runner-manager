import logging
import os
from os.path import exists

import yaml
from marshmallow import fields
from marshmallow import Schema
from settings.exceptions import IncorrectSettingsFile
from settings.exceptions import SettingsFileNotFound

logger = logging.getLogger("runner_manager")


class EnvSettings(object):
    def __init__(self):
        self.setting_file = os.getenv("SETTING_FILE", default="./settings.yml")
        self.github_token = os.getenv("GITHUB_TOKEN")
        self.google_application_credentials = os.getenv(
            "GOOGLE_APPLICATION_CREDENTIALS"
        )
        self.redhat_username = os.getenv("REDHAT_USERNAME")
        self.redhat_password = os.getenv("REDHAT_PASSWORD")
        self.redis_password = os.getenv("REDIS_PASSWORD")


class ExtraRunnerTimer(Schema):
    minutes = fields.Int()
    hours = fields.Int()


class TimeoutRunnerTimer(Schema):
    minutes = fields.Int()
    hours = fields.Int()


class RunnerQuantity(Schema):
    on_demand = fields.Bool(default=False, missing=False)
    min = fields.Int(required=True)
    max = fields.Int(required=True)


class RunnerPool(Schema):
    tags = fields.List(fields.Str(), required=True)
    config = fields.Dict(required=True)
    quantity = fields.Nested(RunnerQuantity, required=True)


class RedisDatabase(Schema):
    host = fields.Str(required=True)
    port = fields.Str(required=True)


class Settings(Schema):
    github_organization = fields.Str(required=True)
    cloud_name = fields.Str(required=True)
    cloud_config = fields.Dict(required=True)
    allowed_ssh_keys = fields.Str(required=False, default="")
    runner_pool = fields.Nested(RunnerPool, many=True, required=True)
    python_config = fields.Str(required=True)
    extra_runner_timer = fields.Nested(ExtraRunnerTimer, required=True)
    timeout_runner_timer = fields.Nested(TimeoutRunnerTimer, required=True)
    redis = fields.Nested(RedisDatabase, required=True)


def setup_settings(settings_file: str) -> dict:
    """Load and checks settings from a yaml file.

    Args:
        - settings_file (str): path of the yaml file to load.

    Raises:
        - SettingsFileNotFound
        - IncorrectSettingsFile if the yaml syntax can't be parsed
        - MalformedSettings if one or more fields from the settings are
                            incorrect (wrong types or missing values)

    Returns:
        The settings as a deserialized yaml object.
    """
    if not exists(settings_file):
        raise SettingsFileNotFound(settings_file)

    with open(settings_file, "r") as f:
        try:
            # read the yaml data as pure string (no conversion)
            data = yaml.load(f, Loader=yaml.BaseLoader)
        except Exception as err:
            raise IncorrectSettingsFile(settings_file) from err

    settings = Settings().load(data)
    for vms in settings["runner_pool"]:
        if vms["quantity"]["on_demand"] is False and vms["quantity"]["min"] == 0:
            logger.warning(f"The Vm {', '.join(vms['tags'])} will never spawn.")
        elif vms["quantity"]["on_demand"] is True and vms["quantity"]["max"] == 0:
            logger.warning(
                f"The VM {', '.join(vms['tags'])} have no spawning limit."
            )  # TODO or the runner crash
        elif vms["quantity"]["on_demand"] is True and vms["quantity"]["min"] > 0:
            logger.warning(
                f"The Vm {', '.join(vms['tags'])} have pre spawn "
                f"and on demand spawn set at the same time."
            )

    return settings
