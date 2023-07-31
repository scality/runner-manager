
from runner_manager.models.base import BaseModel
from runner_manager.backend.base import BaseBackend
from redis_om import Field
from typing import Optional, List



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

    # backend will be a parameter set as a string for user but will be a BaseBackend object
    # the runnergroup will return the according backend object (docker, gcloud, aws, etc)
    backend: Optional[str] or Optional[Backend] = Field(index=True, full_text_search=True, default="docker")
    backend_config: Optional[dict] = Field(index=True, full_text_search=True, default={})


    def __init__(self, **data):
        super().__init__(**data)
        self.backend = BaseBackend.get_backend(self.backend)

    def __str__(self):
        return f"{self.name} ({self.backend})"

    def __repr__(self):
        return f"{self.name} ({self.backend})"

    def __hash__(self):
        return hash(self.id)

    def __eq__(self, other):
        return self.id == other.id

