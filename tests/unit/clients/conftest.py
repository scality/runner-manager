import pytest

from runner_manager.clients.github import RunnerGroup


@pytest.fixture()
def runner_group() -> RunnerGroup:
    return RunnerGroup(id=2, name="octo-runner-group")


@pytest.fixture()
def org() -> str:
    return "octo-org"
