from pytest import fixture

from runner_manager.dependencies import get_settings
from runner_manager.models.settings import Settings


@fixture(scope="session", autouse=True)
def settings() -> Settings:
    settings = get_settings()
    return settings
