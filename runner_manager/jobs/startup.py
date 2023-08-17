"""Jobs to run on startup."""

from typing import List

from redis_om import Migrator

from runner_manager.clients.github import GitHub
from runner_manager.dependencies import get_github, get_settings
from runner_manager.logging import log
from runner_manager.models.runner_group import RunnerGroup
from runner_manager.models.settings import Settings


def create_runner_groups(settings: Settings, github: GitHub):
    runner_groups_configs = settings.runner_groups
    existing_groups: List[RunnerGroup] = RunnerGroup.find().all()

    for runner_group_config in runner_groups_configs:
        if runner_group_config.name not in [group.name for group in existing_groups]:
            runner_group: RunnerGroup = RunnerGroup(**runner_group_config.dict())
            runner_group.save(github=github)
        else:
            runner_group: RunnerGroup = RunnerGroup.find(
                RunnerGroup.name == runner_group_config.name
            ).first()

            runner_group.update(**runner_group_config.dict())
            existing_groups.remove(runner_group)
    for runner_group in existing_groups:
        runner_group.delete(pk=runner_group.pk, github=github)


def startup(settings: Settings = get_settings(), github: GitHub = get_github()):
    """Bootstrap the application."""
    log.info("Startup complete.")

    Migrator().run()
    create_runner_groups(settings, github)
