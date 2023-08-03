from pytest import fixture

from runner_manager.backend.base import BaseBackend


@fixture()
def backend(runner_group) -> BaseBackend:
    """Fixture for backend."""
    return runner_group.backend
