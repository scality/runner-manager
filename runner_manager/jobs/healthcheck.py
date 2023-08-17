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
from runner_manager.models.runner import RunnerStatus
from runner_manager.models.settings import Settings


def healthchecks(runner_group: RunnerGroup, settings: Settings = get_settings()):
    runners: List[Runner] | List[RedisModel] = runner_group.get_runners()
    github: GitHub = get_github()
    for runner in runners:
        log.info(f"Health checking runner {runner.name}")
        if runner.id is not None:
            github_runner: GitHubRunner = (
                github.rest.actions.get_self_hosted_runner_for_org(
                    runner_group.organization, runner.id
                ).parsed_data
            )
            log.info(
                f"Updating status Runner {runner.name} status: {github_runner.status}"
            )
            update_status(runner, github_runner)
            log.info(f"Runner {runner.name} status updated")
            if runner.time_to_live_expired(settings.time_to_live):
                runner_group.delete_runner(runner)
                log.info(f"Runner {runner.name} deleted")
            elif runner.time_to_start_expired(settings.timeout_runner):
                runner_group.delete_runner(runner)
                log.info(f"Runner {runner.name} deleted")
    while runner_group.need_new_runner:
        token_response: Response[
            AuthenticationToken
        ] = github.rest.actions.create_registration_token_for_org(
            org=runner_group.organization
        )
        token: AuthenticationToken = token_response.parsed_data
        log.info("Registration token created.")
        runner: Runner = runner_group.create_runner(token)
        log.info(f"Runner {runner.name} created")
    runner_group.save()


def update_status(runner: Runner, github_runner: GitHubRunner) -> Runner:
    runner.status = RunnerStatus(github_runner.status)
    runner.busy = github_runner.busy
    runner.updated_at = datetime.now()
    return runner.save()
