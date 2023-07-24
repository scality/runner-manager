from abc import ABC
from typing import List

from runner_manager.models.runner import Runner

class BackendBase(ABC):
    """Base class for runners backend.

    Runners backend are responsible for managing runners instances.
    """

    def create(self, runner: Runner) -> Runner:
        """Create a runner instance.

        Args:
            runner (Runner): Runner instance to be created.
        """
        raise NotImplementedError

    def delete(self, runner: Runner) -> Runner:
        """Delete a runner instance.

        Args:
            runner (Runner): Runner instance to be deleted.
        """
        raise NotImplementedError

    def update(self, runner: Runner) -> Runner:
        """Update a runner instance.

        Args:
            runner (Runner): Runner instance to be updated.
        """
        raise NotImplementedError

    def get(self, instance_id: int) -> Runner:
        """Get a runner instance.

        Args:
            instance_id (int): Runner instance id.

        Returns:
            Runner: Runner instance.
        """
        raise NotImplementedError

    def list(self) -> List[Runner]:
        """List all runner instances.

        Returns:
            list: List of runner instances.
        """
        raise NotImplementedError