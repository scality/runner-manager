from datetime import datetime, timedelta

from githubkit.rest.models import AuthenticationToken
from hypothesis import given, settings
from hypothesis import strategies as st
from redis_om import Migrator
from rq import Queue

from runner_manager.clients.github import GitHub
from runner_manager.jobs import healthcheck
from runner_manager.models.runner import Runner, RunnerStatus
from runner_manager.models.runner_group import RunnerGroup
from runner_manager.models.settings import Settings

from ...strategies import GithubRunnerStrategy, SettingsStrategy


@given(
    github_runners=st.lists(GithubRunnerStrategy, min_size=1),
    settings=SettingsStrategy,
)
@settings(max_examples=10)
def test_healthchecks_hypothesis(
    github_runners: list, settings: Settings, runner_group: RunnerGroup, github: GitHub
):
    # create github runners
    for github_runner in github_runners:
        print(github_runner.name)
        runner = Runner(
            id=github_runner.id,
            name=f"runner_{github_runner.id}",
            status=github_runner.status,
            busy=github_runner.busy,
            runner_group_name=runner_group.name,
            runner_group_id=runner_group.id,
        )
        # TODO: might be missing some sort of started at if runner.status is online
        runner.save()
    runner_group.save()
    runner_group.healthcheck(settings.time_to_live, settings.timeout_runner, github)
    for runner in runner_group.get_runners():
        assert runner.time_to_start_expired(settings.timeout_runner) is False
        assert runner.time_to_live_expired(settings.time_to_live) is False


def test_group_healthcheck(
    runner_group: RunnerGroup, settings: Settings, github: GitHub, runner_token
):
    runner_group.save(github=github)
    runner_tts: Runner = runner_group.create_runner(runner_token)
    assert runner_tts is not None
    runner_tts.created_at = datetime.now() - timedelta(
        minutes=settings.timeout_runner + 1
    )
    runner_tts.save()
    runner_ttl: Runner = runner_group.create_runner(runner_token)
    assert runner_ttl is not None
    runner_ttl.status = RunnerStatus.online
    runner_ttl.started_at = datetime.now() - timedelta(
        minutes=settings.time_to_live + 1
    )
    runner_ttl.save()
    Migrator().run()
    assert len(runner_group.get_runners()) == 2
    runner_group.healthcheck(settings.time_to_live, settings.timeout_runner, github)
    assert len(runner_group.get_runners()) == 0


def test_need_new_runner_healthcheck(
    runner_group: RunnerGroup, settings: Settings, github: GitHub
):
    runner_group.max = 2
    runner_group.min = 1
    runner_group.save()
    assert runner_group.need_new_runner is True
    runner_group.healthcheck(settings.time_to_live, settings.timeout_runner, github)
    assert runner_group.need_new_runner is False
    assert len(runner_group.get_runners()) == 1


def test_time_to_start(runner: Runner, settings: Settings):
    runner.created_at = datetime.now() - timedelta(minutes=settings.timeout_runner + 1)
    runner.status = RunnerStatus.offline
    assert runner.time_to_start_expired(timeout=settings.timeout_runner) is True

    runner.created_at = datetime.now() - timedelta(minutes=settings.timeout_runner - 1)
    assert runner.time_to_start_expired(timeout=settings.timeout_runner) is False


def test_time_to_live(runner: Runner, settings: Settings):
    runner.started_at = datetime.now() - timedelta(minutes=settings.time_to_live + 1)
    runner.status = RunnerStatus.online
    assert runner.time_to_live_expired(settings.time_to_live) is True

    runner.started_at = datetime.now() - timedelta(minutes=settings.time_to_live - 1)
    assert runner.time_to_live_expired(settings.time_to_live) is False


def test_need_new_runner(runner_group: RunnerGroup, runner_token: AuthenticationToken):
    runner_group.max = 2
    runner_group.min = 1
    runner_group.save()
    assert runner_group.need_new_runner is True
    runner_group.create_runner(runner_token)
    assert runner_group.need_new_runner is False


def test_healthcheck_job(
    runner_group: RunnerGroup, settings: Settings, queue: Queue, runner_token
):
    runner_group.save()
    queue.enqueue(
        healthcheck.group,
        runner_group.pk,
        settings.time_to_live,
        settings.timeout_runner,
    )
    assert len(runner_group.get_runners()) == 0
    runner_group.create_runner(runner_token)
    queue.enqueue(
        healthcheck.group,
        runner_group.pk,
        settings.time_to_live,
        settings.timeout_runner,
    )
    assert len(runner_group.get_runners()) == 1
