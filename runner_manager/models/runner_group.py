from typing import List, Optional, Union

from pydantic import BaseModel as PydanticBaseModel
from pydantic import Field as PydanticField
from redis_om import Field, JsonModel, RedisModel
from typing_extensions import Annotated

from runner_manager.backend.base import BaseBackend
from runner_manager.backend.docker import DockerBackend
from runner_manager.models.backend import InstanceConfig
from runner_manager.models.runner import Runner, RunnerLabel


class BaseRunnerGroup(PydanticBaseModel):
    name: str
    organization: Optional[str] = None
    repository: Optional[str] = None
    allows_public_repositories: Optional[bool] = True
    default: Optional[bool] = None
    runners_url: Optional[str] = None
    restricted_to_workflows: Optional[bool] = None
    selected_workflows: Optional[List[str]] = None
    workflow_restrictions_read_only: Optional[bool] = None
    selected_repository_ids: Optional[List[int]] = None
    runners: Optional[List[int]] = None
    max: Optional[int] = Field(ge=1, default=20)
    min: Optional[int] = Field(ge=0, default=0)
    labels: List[str]

    backend: Annotated[
        Union[BaseBackend, DockerBackend], PydanticField(..., discriminator="name")
    ]
    instance_config: Optional[InstanceConfig] = None


class RunnerGroup(BaseRunnerGroup, JsonModel):

    id: Optional[int] = Field(index=True, default=None)
    name: str = Field(index=True, full_text_search=True)
    manager: Optional[str] = Field(index=True, full_text_search=True)
    organization: Optional[str] = Field(index=True, full_text_search=True)
    repository: Optional[str] = Field(index=True, full_text_search=True)
    max: Optional[int] = Field(index=True, ge=1, default=20)
    min: Optional[int] = Field(index=True, ge=0, default=0)

    def __post_init_post_parse__(self):
        """Post init."""
        if self.backend.manager is None:
            self.backend.manager = self.manager

    @property
    def runner_labels(self) -> List[RunnerLabel]:
        """Return self.labels as a list of RunnerLabel."""
        return [RunnerLabel(name=label) for label in self.labels]

    def get_runners(self) -> List[Runner] | List[RedisModel]:
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
        runner.labels = self.runner_labels
        runner.manager = self.manager
        return self.backend.create(runner)

    def delete_runner(self, runner: Runner) -> int:
        """Delete a runner instance.

        Returns:
            Runner: Runner instance.
        """
        return self.backend.delete(runner)
