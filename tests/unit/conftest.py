from pytest import fixture
from pytest_redis import factories
from redis_om import Migrator, get_redis_connection
from rq import Queue, SimpleWorker

from runner_manager.dependencies import get_settings
from runner_manager.models.runner import Runner
from runner_manager.models.runner_group import RunnerGroup
from runner_manager.models.settings import Settings


@fixture(scope="session", autouse=True)
def settings() -> Settings:
    settings = get_settings()
    return settings


@fixture(scope="session", autouse=True)
def redis():
    redis_my_proc = factories.redis_proc()
    redis_connection = factories.redisdb("redis_my_proc")
    Migrator().run()
    yield redis_connection
    # Clean up if needed


@fixture(scope="session", autouse=True)
def worker(queue):
    worker = SimpleWorker([queue], connection=queue.connection)
    worker.work(burst=True)
    return worker


@fixture(scope="session")
def queue(redis) -> Queue:
    return Queue(connection=redis)


@fixture()
def runner() -> Runner:
    runner = Runner(
        name="test", runner_group_id=1, status="online", busy=False, labels=[]
    )
    Runner.delete(runner.pk)
    return runner


@fixture(scope="function", autouse=True)
def runner_group() -> RunnerGroup:
    runner_group = RunnerGroup(
        id=1,
        name="test",
        organization="test",
        backend={"name": "base"},
        labels=[
            "label",
        ],
    )
    # Ensure that the runner group has no runners.
    for runner in runner_group.get_runners():
        print(f"deleted runner {runner.name}")
        Runner.delete(runner.pk)
    return runner_group
