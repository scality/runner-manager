
from pytest import fixture
from runner_manager.backend.base import BaseBackend

@fixture()
def backend() -> BaseBackend:
    """Fixture for backend."""
    return BaseBackend.get_backend(name="base", config=None)
