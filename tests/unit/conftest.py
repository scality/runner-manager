from uuid import uuid4

from pytest import fixture
from redis import Redis
from redis_om import Migrator, get_redis_connection
from rq import Queue

from hypothesis import settings as hypothesis_settings
from hypothesis import HealthCheck
from runner_manager import Runner, RunnerGroup, Settings


hypothesis_settings.register_profile(
    "unit",
    suppress_health_check=[HealthCheck.function_scoped_fixture],
    max_examples=50,
)
hypothesis_settings.load_profile("unit")

@fixture(scope="function", autouse=True)
def settings():
    """Monkeypatch settings to use the test config."""

    settings = Settings(
        name=uuid4().hex,
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
    for key in redis.scan_iter(f"{settings.name}:*"):
        print(f"deleted key {key}")
        redis.delete(key)
    Migrator().run()

    Runner.Meta.database = redis
    RunnerGroup.Meta.database = redis
    return redis


@fixture(scope="function")
def queue(redis) -> Queue:
    """Return a RQ Queue instance.

    The Queue is configured with is_async=False to ensure that jobs are executed
    synchronously and do not require a worker to be running.

    """
    return Queue(is_async=False, connection=redis)


@fixture()
def runner(settings) -> Runner:
    runner: Runner = Runner(
        name="test",
        runner_group_id=1,
        status="online",
        busy=False,
        labels=[],
        manager=settings.name,
    )
    assert runner.Meta.global_key_prefix == settings.name
    Runner.delete(runner.pk)
    return runner


@fixture()
def runner_group(settings) -> RunnerGroup:
    runner_group = RunnerGroup(
        id=1,
        name="test",
        manager=settings.name,
        organization="test",
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
