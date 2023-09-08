import logging

from runner_manager import RunnerGroup
from runner_manager.clients.github import GitHub
from runner_manager.dependencies import get_github

log = logging.getLogger(__name__)


def runner(group: RunnerGroup) -> str | None:
    """Job to create a runner within a group.

    Args:
        RunnerGroup: Runner group to create a runner in
    """
    github: GitHub = get_github()
    runner = group.create_runner(github)
    if runner is not None:
        return runner.pk
