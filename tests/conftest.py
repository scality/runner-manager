from uuid import uuid4

from pytest import fixture
from redis import Redis
from redis_om import Migrator, get_redis_connection
from rq import Queue
from rq_scheduler import Scheduler

from runner_manager import Runner, RunnerGroup, Settings
from runner_manager.backend.base import BaseBackend
from runner_manager.models.runner_group import BaseRunnerGroup


@fixture(scope="function", autouse=True)
def settings():
    """Monkeypatch settings to use the test config."""

    settings = Settings(
        name=uuid4().hex,
        runner_groups=[
            BaseRunnerGroup(
                name="test",
                organization="octo-org",
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
def queue(settings) -> Queue:
    """Return a RQ Queue instance.

    The Queue is configured with is_async=False to ensure that jobs are executed
    synchronously and do not require a worker to be running.

    """
    redis: Redis = get_redis_connection(
        url=settings.redis_om_url, decode_responses=False
    )
    return Queue(is_async=False, connection=redis)


@fixture(scope="function")
def scheduler(queue) -> Scheduler:
    """Return a RQ Scheduler instance."""
    return Scheduler(queue=queue, connection=queue.connection)


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
