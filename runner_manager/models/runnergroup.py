from typing import List, Optional

from redis_om import Field

from runner_manager.backend.base import Backends, BaseBackend
from runner_manager.models.base import BaseModel
from runner_manager.models.runner import Runner


class RunnerGroup(BaseModel):
    id: Optional[int] = Field(index=True, ge=0)
    name: str = Field(index=True, full_text_search=True)
    organization: Optional[str] = Field(index=True, full_text_search=True)
    repository: Optional[str] = Field(index=True, full_text_search=True)
    allows_public_repositories: Optional[bool] = True
    default: Optional[bool] = None
    runners_url: Optional[str] = None
    restricted_to_workflows: Optional[bool] = None
    selected_workflows: Optional[List[str]] = None
    workflow_restrictions_read_only: Optional[bool] = None
    selected_repository_ids: Optional[List[int]] = None
    runners: Optional[List[int]] = None
    max: Optional[int] = Field(index=True, ge=0, default=20)
    min: Optional[int] = Field(index=True, ge=0, default=0)
    labels: Optional[List[str]] = Field(index=True, full_text_search=True, default=[])

    backend: Backends = Field(index=True, full_text_search=True, default="docker")
    backend_config: Optional[dict] = Field(
        index=True, full_text_search=True, default={}
    )

    def __init__(self, **data):
        super().__init__(**data)

    def __str__(self):
        return f"{self.name} ({self.backend})"

    def __repr__(self):
        return f"{self.name} ({self.backend})"

    def __hash__(self):
        return hash(self.id)

    def __eq__(self, other):
        return self.id == other.id

    def get_backend(self) -> BaseBackend:
        """Get the backend class.

        Returns:
            BaseBackend: Backend class.
        """
        return BaseBackend.get_backend(runner_group=self)

    def get_runners(self) -> List[Runner]:
        """Get the runners.

        Returns:
            List[Runner]: List of runners.
        """
        return Runner.find(Runner.runner_group_id == self.id).all()

    def create_runner(self, runner: Runner) -> Runner:
        """Create a runner instance.

        Returns:
            Runner: Runner instance.
        """
        runner.runner_group_id = self.id
        runner.labels = self.labels
        return self.get_backend().create(runner)
