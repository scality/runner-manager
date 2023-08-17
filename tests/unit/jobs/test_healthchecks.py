from datetime import datetime, timedelta

from githubkit.rest.models import AuthenticationToken

from runner_manager.jobs.healthcheck import healthchecks
from runner_manager.models.runner import Runner, RunnerStatus
from runner_manager.models.runner_group import RunnerGroup
from runner_manager.models.settings import Settings


def test_healthchecks(
    runner_group: RunnerGroup, settings: Settings, runner_token: AuthenticationToken
):
    runner_group.save()
    runner: Runner = runner_group.create_runner(runner_token)
    healthchecks(runner_group, settings)


def test_time_to_start(runner: Runner, settings: Settings):
    runner.created_at = datetime.now() - timedelta(minutes=settings.timeout_runner + 1)
    runner.status = RunnerStatus.offline
    assert runner.time_to_start_expired(timeout=settings.timeout_runner) is True

    runner.created_at = datetime.now() - timedelta(minutes=settings.timeout_runner - 1)
    assert runner.time_to_start_expired(timeout=settings.timeout_runner) is False


def test_time_to_live(runner: Runner, settings: Settings):
    runner.updated_at = datetime.now() - timedelta(minutes=settings.time_to_live + 1)
    runner.status = RunnerStatus.online
    assert runner.time_to_live_expired(settings.time_to_live) is True

    runner.updated_at = datetime.now() - timedelta(minutes=settings.time_to_live - 1)
    assert runner.time_to_live_expired(settings.time_to_live) is False


def test_need_new_runner(
    runner_group: RunnerGroup, settings: Settings, runner_token: AuthenticationToken
):
    runner_group.max = 2
    runner_group.min = 1
    runner_group.save()
    assert runner_group.need_new_runner is True
    runner: Runner = runner_group.create_runner(runner_token)
    assert runner_group.need_new_runner is False
