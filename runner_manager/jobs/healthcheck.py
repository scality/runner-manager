from datetime import datetime, timedelta
from typing import List

from githubkit import Response
from githubkit.rest.models import AuthenticationToken
from githubkit.rest.models import Runner as GitHubRunner
from redis_om import RedisModel

from runner_manager import Runner, RunnerGroup
from runner_manager.clients.github import GitHub
from runner_manager.dependencies import get_github, get_settings
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

def update_status(runner: Runner, github_runner: GitHubRunner) -> Runner:
    runner.status = RunnerStatus(github_runner.status)
    runner.busy = github_runner.busy
    runner.updated_at = datetime.now()
    return runner.save()
