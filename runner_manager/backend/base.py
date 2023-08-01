from abc import ABC
from enum import Enum
from typing import List

from runner_manager.models.base import BaseModel
from runner_manager.models.runner import Runner
from runner_manager.models.runnergroup import RunnerGroup


class Backends(str, Enum):
    base = "base"
    docker = "docker"
    gcloud = "gcloud"
    aws = "aws"


class BaseBackend(ABC, BaseModel):
    """Base class for runners backend.

    Runners backend are responsible for managing runners instances.

    They take a RunnerGroup as input.
    """

    runner_group: RunnerGroup

    @property
    def name(self) -> Backends:
        """Name of the backend.

        Returns:
            str: Name of the backend.
        """
        return self.runner_group.backend

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
    def get_backend(cls, runner_group: RunnerGroup) -> "BaseBackend":
        """Get a runner backend.

        Args:
            backend (str): Runner backend name.

        Returns:
            BaseBackend: Runner backend.
        """

        if runner_group.backend == Backends.base:
            return BaseBackend()
        else:
            raise NotImplementedError
