import logging
from datetime import timedelta

from redis_om import NotFoundError

from runner_manager import RunnerGroup
from runner_manager.clients.github import GitHub
from runner_manager.dependencies import get_github

log = logging.getLogger(__name__)


def group(pk: str, time_to_live: timedelta, timeout_runner: timedelta):
    """Job to healthcheck a runner group.

    Args:
        pk (str): Runner group primary key
        time_to_live (int): Time to live in minutes
        timeout_runner (int): Timeout in minutes
    """
    github: GitHub = get_github()
    try:
        group = RunnerGroup.get(pk)
        group.healthcheck(time_to_live, timeout_runner, github)
    except NotFoundError:
        log.error(f"Runner group {pk} not found")
