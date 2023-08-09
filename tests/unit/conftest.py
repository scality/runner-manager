from uuid import uuid4

from pytest import fixture
from redis import Redis
from redis_om import Migrator, get_redis_connection
from rq import Queue

from runner_manager.dependencies import get_settings
from runner_manager.models.runner import Runner
from runner_manager.models.runner_group import RunnerGroup
from runner_manager.models.settings import Settings


@fixture(scope="function", autouse=True)
def settings(monkeypatch):
    """Monkeypatch settings to use the test config."""

    settings = Settings(
        name=uuid4().hex,
    )
    get_settings.cache_clear()
    monkeypatch.setattr("runner_manager.dependencies.get_settings", lambda: settings)
    monkeypatch.setattr(
        "runner_manager.models.base.BaseModel.Meta.global_key_prefix", settings.name
    )
    monkeypatch.setattr(
        "runner_manager.models.runner.Runner.Meta.global_key_prefix", settings.name
    )
    monkeypatch.setattr(
        "runner_manager.models.runner_group.RunnerGroup.Meta.global_key_prefix",
        settings.name,
    )
    return settings


@fixture(scope="function", autouse=True)
def redis(settings, monkeypatch):
    """Monkeypatch redis connections to use the test config."""
    # Ensure that the redis connection is closed before the test starts.
    redis: Redis = get_redis_connection(
        url=settings.redis_om_url, decode_responses=True
    )
    for key in redis.scan_iter(f"{settings.name}:*"):
        print(f"deleted key {key}")
        redis.delete(key)
    Migrator().run()

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
        name="test", runner_group_id=1, status="online", busy=False, labels=[]
    )
    assert runner.Meta.global_key_prefix == settings.name
    Runner.delete(runner.pk)
    return runner


@fixture()
def runner_group(settings) -> RunnerGroup:
    runner_group = RunnerGroup(
        id=1,
        name="test",
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
