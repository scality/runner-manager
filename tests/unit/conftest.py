from datetime import timedelta
from uuid import uuid4

import httpx
from githubkit import Response
from githubkit.config import Config
from githubkit.rest.models import AuthenticationToken
from hypothesis import HealthCheck
from hypothesis import settings as hypothesis_settings
from pytest import fixture
from redis import Redis
from redis_om import Migrator, get_redis_connection
from rq import Queue

from runner_manager import Runner, RunnerGroup, Settings
from runner_manager.backend.base import BaseBackend
from runner_manager.clients.github import GitHub
from runner_manager.models.runner_group import BaseRunnerGroup

hypothesis_settings.register_profile(
    "unit",
    suppress_health_check=[HealthCheck.function_scoped_fixture],
    max_examples=10,
    deadline=timedelta(seconds=1),
)
hypothesis_settings.load_profile("unit")


@fixture(scope="function", autouse=True)
def settings():
    """Monkeypatch settings to use the test config."""

    settings = Settings(
        name=uuid4().hex,
        runner_groups=[
            BaseRunnerGroup(
                name="test",
                labels=[
                    "label",
                ],
                backend=BaseBackend(config=None, instance_config=None),
            )
        ],
        github_token="test",
        github_base_url="http://localhost:4010",
    )
    Runner.Meta.global_key_prefix = settings.name
    RunnerGroup.Meta.global_key_prefix = settings.name
    return settings


@fixture(scope="function", autouse=True)
def redis(settings):
    """Monkeypatch redis connections to use the test config."""
    # Ensure that the redis connection is closed before the test starts.
    redis: Redis = get_redis_connection(
        url=settings.redis_om_url, decode_responses=True
    )

    Migrator().run()

    Runner.Meta.database = redis
    RunnerGroup.Meta.database = redis
    Runner.delete_many(Runner.find().all())
    RunnerGroup.delete_many(RunnerGroup.find().all())

    return redis


@fixture(scope="function")
def queue(redis) -> Queue:
    """Return a RQ Queue instance.

    The Queue is configured with is_async=False to ensure that jobs are executed
    synchronously and do not require a worker to be running.

    """
    return Queue(is_async=False, connection=redis)


@fixture()
def github(settings) -> GitHub:
    """
    Return a GitHub client configured with:

    - The mock server as base_url.
    - Accept application/json as response from the server.

    """

    config = Config(
        base_url=httpx.URL(settings.github_base_url),
        accept="*/*",
        user_agent="runner-manager",
        follow_redirects=True,
        timeout=httpx.Timeout(5.0),
    )

    return GitHub(config=config)


@fixture()
def runner(settings) -> Runner:
    runner: Runner = Runner(
        id=1,
        name="test",
        runner_group_id=1,
        status="online",
        busy=False,
        labels=[],
        manager=settings.name,
    )
    assert runner.Meta.global_key_prefix == settings.name
    Runner.delete_many(Runner.find().all())
    return runner


@fixture()
def runner_group(settings) -> RunnerGroup:
    runner_group = RunnerGroup(
        id=1,
        name="test",
        manager=settings.name,
        organization="octo-org",
        backend={"name": "base"},
        labels=[
            "label",
        ],
    )
    assert runner_group.Meta.global_key_prefix == settings.name
    # Ensure that the runner group has no runners.
    for runner in runner_group.get_runners():
        print(f"deleted runner {runner.name}")
        Runner.delete(runner.pk)
    return runner_group


@fixture()
def runner_token(runner_group: RunnerGroup, github: GitHub) -> AuthenticationToken:
    token: Response[
        AuthenticationToken
    ] = github.rest.actions.create_registration_token_for_org(
        org=runner_group.organization
    )
    return token.parsed_data
