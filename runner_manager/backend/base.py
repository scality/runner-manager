from abc import ABC
from typing import List, Enum
from runner_manager.models.runner import Runner
from runner_manager.models.base import BaseModel
from redis_om import Field


class Backends(str, Enum):

    base = "base"
    docker = "docker"
    gcloud = "gcloud"
    aws = "aws"


class BaseBackend(ABC, BaseModel):
    """Base class for runners backend.

    Runners backend are responsible for managing runners instances.
    """

    name: Backends = Field(index=True, full_text_search=True, default=Backends.base)



    def create(self, runner: Runner) -> Runner:
        """Create a runner instance.

        Args:
            runner (Runner): Runner instance to be created.
        """
        return runner.save()

    def delete(self, runner: Runner) -> Runner:
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
        return Runner.find(Runner.backend_instance == instance).first()

    def list(self) -> List[Runner]:
        """List all runner instances.

        Returns:
            list: List of runner instances.
        """
        raise NotImplementedError

    @classmethod
    def get_backend(cls, backend: Backends):
        """Get a runner backend.

        Args:
            backend (str): Runner backend name.

        Returns:
            BaseBackend: Runner backend.
        """

        if backend == Backends.base:
            return BaseBackend()
        else:
            raise NotImplementedError