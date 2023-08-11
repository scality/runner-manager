from typing import List, Literal, Optional

from pydantic import BaseModel, Field
from redis_om import NotFoundError

from runner_manager.models.backend import BackendConfig, Backends, InstanceConfig
from runner_manager.models.runner import Runner


class BaseBackend(BaseModel):
    """Base class for runners backend.

    Runners backend are responsible for managing runners instances.

    They take a RunnerGroup as input.
    """

    name: Literal[Backends.base] = Field(default=Backends.base)
    config: Optional[BackendConfig]
    manager: Optional[str] = None
    instance_config: Optional[InstanceConfig] = Field(default=None)

    # Inherited classes will have a client property configured
    # to interact with the backend.

    @property
    def client(self):
        """Client to interact with the backend."""
        raise NotImplementedError

    def create(self, runner: Runner) -> Runner:
        """Create a runner instance.

        Args:
            runner (Runner): Runner instance to be created.
        """
        runner.backend = self.name
        if runner.instance_id is None:
            runner.instance_id = runner.pk
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

    def get(self, instance_id: str) -> Runner:
        """Get a runner instance.

        Args:
            instance_id (str): Runner instance id.

        Returns:
            Runner: Runner instance.
        """
        try:
            runner: Runner = Runner.find(Runner.instance_id == instance_id).first()
        except NotFoundError as exception:
            raise NotFoundError(f"Instance {instance_id} not found.") from exception

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
