from pytest import fixture

from runner_manager.backend.base import BaseBackend
from runner_manager.models.backend import Backends


@fixture()
def backend() -> BaseBackend:
    """Fixture for backend."""
    return BaseBackend.get_backend(name=Backends.base, config=None)
