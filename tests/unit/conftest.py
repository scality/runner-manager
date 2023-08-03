from pytest import fixture

from runner_manager.dependencies import get_settings
from runner_manager.models.runner import Runner
from runner_manager.models.settings import Settings


@fixture(scope="session", autouse=True)
def settings() -> Settings:
    settings = get_settings()
    return settings


@fixture()
def runner() -> Runner:
    runner = Runner(
        name="test", runner_group_id=1, status="online", busy=False, labels=[]
    )
    Runner.delete(runner.pk)
    return runner
