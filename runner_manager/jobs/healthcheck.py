from typing import List

from runner_manager import RunnerGroup
from runner_manager.logging import log
from runner_manager.models.runner_group import RunnerGroup


def healthchecks(runner_groups: List[RunnerGroup]):
    """Healthchecks runner groups."""
    for runner_group in runner_groups:
        log.info(f"Checking health for runner group {runner_group.name}")
        if runner_group.backend.manager is None:
            log.error(f"Runner group {runner_group.name} has no backend manager")
            continue
        try:
            runner_group.healthcheck()
        except Exception as e:
            log.error(f"Runner group {runner_group.name} healthcheck failed: {e}")
        else:
            runner_group.save()
            log.info(f"Runner group {runner_group.name} healthcheck succeeded")
