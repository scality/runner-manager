import logging

from redis_om import NotFoundError

from runner_manager import RunnerGroup
from runner_manager.clients.github import GitHub
from runner_manager.dependencies import get_github

log = logging.getLogger(__name__)


def group(pk: str):
    """Job to reset a runner group.

    Args:
        pk (str): Runner group primary key
    """
    github: GitHub = get_github()
    try:
        group = RunnerGroup.get(pk)
    except NotFoundError:
        log.error(f"Runner group {pk} not found")
        raise
    else:
        group.reset(github)
