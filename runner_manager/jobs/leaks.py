import logging

from redis_om import NotFoundError

from runner_manager import RunnerGroup

log = logging.getLogger(__name__)


def runner_leaks(pk: str) -> bool:
    """
    Job that will look for leaks in the runner group
    and for now it will just log the runner's name that
    could be considered as a leak.

    returns:
        bool: True if a leak was found, False otherwise
    """

    try:
        group: RunnerGroup = RunnerGroup.get(pk)
    except NotFoundError:
        log.error(f"Runner group {pk} not found")
        return False
    backend_runners = group.backend.list()
    group_runners = group.get_runners()
    if len(backend_runners) > len(group_runners):
        log.warning(f"Runner group {pk} has leaks")
        for runner in backend_runners:
            if runner not in group_runners:
                log.warning(f"Runner {runner} could be considered as a leak")
        return True
    else:
        return False
