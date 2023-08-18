from typing import List

from runner_manager import RunnerGroup, Settings
from runner_manager.clients.github import GitHub
from runner_manager.dependencies import get_github, get_settings
from runner_manager.logging import log


def healthchecks(runner_groups: List[RunnerGroup]):
    """Healthchecks runner groups."""
    settings: Settings = get_settings()
    github: GitHub = get_github()
    for runner_group in runner_groups:
        log.info(f"Checking health for runner group {runner_group.name}")
        if runner_group.backend.manager is None:
            log.error(f"Runner group {runner_group.name} has no backend manager")
            continue
        try:
            runner_group.healthcheck(
                settings.time_to_live, settings.timeout_runner, github=github
            )
        except Exception as e:
            log.error(f"Runner group {runner_group.name} healthcheck failed: {e}")
        else:
            log.info(f"Runner group {runner_group.name} healthcheck succeeded")
