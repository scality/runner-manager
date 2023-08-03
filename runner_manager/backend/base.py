from typing import List, Optional

from pydantic import BaseModel
from redis_om import NotFoundError

from runner_manager.models.backend import BackendConfig, Backends
from runner_manager.models.runner import Runner


class BaseBackend(BaseModel):
    """Base class for runners backend.

    Runners backend are responsible for managing runners instances.

    They take a RunnerGroup as input.
    """

    name: Backends = Backends.base
    config: Optional[BackendConfig]

    def create(self, runner: Runner) -> Runner:
        """Create a runner instance.

        Args:
            runner (Runner): Runner instance to be created.
        """
        runner.backend = self.name
        if runner.backend_instance is None:
            runner.backend_instance = runner.pk
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
        try:
            runner: Runner = Runner.find(Runner.backend_instance == instance).first()
        except NotFoundError as exception:
            raise NotFoundError(f"Instance {instance} not found.") from exception

        return runner

    def list(self) -> List[Runner]:
        """List all runner instances.

        Returns:
            list: List of runner instances.
        """
        try:
            runners: List[Runner] = Runner.find(Runner.backend == self.name).all()
        except NotFoundError as exception:
            raise NotFoundError(
                f"No runners found for {self.name} backend."
            ) from exception
        return runners

    @classmethod
    def get_backend(
        cls, name: Backends, config: Optional[BackendConfig]
    ) -> "BaseBackend":
        """Get a runner backend.

        Args:
            backend (str): Runner backend name.

        Returns:
            BaseBackend: Runner backend.
        """

        if name == Backends.base:
            return BaseBackend(config=config)
        else:
            raise NotImplementedError
