from abc import ABC
from typing import List, Optional

from runner_manager.models.backend import Backends
from runner_manager.models.runner import Runner


class BaseBackend(ABC):
    """Base class for runners backend.

    Runners backend are responsible for managing runners instances.

    They take a RunnerGroup as input.
    """

    def __init__(self, name: Backends, config: Optional[dict]):
        """Initialize a runner backend.

        Args:
            name (str): Runner backend name.
            config (dict): Runner backend config.
        """
        self.name = name
        self.config = config

    def create(self, runner: Runner) -> Runner:
        """Create a runner instance.

        Args:
            runner (Runner): Runner instance to be created.
        """
        return runner.save()

    def delete(self, runner: Runner) -> int:
        """Delete a runner instance.

        Args:
            runner (Runner): Runner instance to be deleted.
        """
        return Runner.delete(runner.pk)

    def update(self, runner: Runner) -> Runner:
        """Update a runner instance.

        Args:
            runner (Runner): Runner instance to be updated.
        """
        return runner.save()

    def get(self, instance: int) -> Runner:
        """Get a runner instance.

        Args:
            instance_id (int): Runner instance id.

        Returns:
            Runner: Runner instance.
        """
        runner: Runner = Runner.find(Runner.backend_instance == instance).first()
        return runner

    def list(self) -> List[Runner]:
        """List all runner instances.

        Returns:
            list: List of runner instances.
        """
        raise NotImplementedError

    @classmethod
    def get_backend(cls, name: Backends, config: Optional[dict]) -> "BaseBackend":
        """Get a runner backend.

        Args:
            backend (str): Runner backend name.

        Returns:
            BaseBackend: Runner backend.
        """

        if name == Backends.base:
            return BaseBackend(name, config)
        else:
            raise NotImplementedError
