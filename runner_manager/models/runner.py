from datetime import datetime
from enum import Enum
from typing import List, Literal, Optional, Union

from pydantic import BaseModel as PydanticBaseModel
from redis_om import Field

from runner_manager.models.base import BaseModel

# Ideally the runner model would have been inherited
# from githubkit.rest.models.Runner, like the following:
# class Runner(BaseModel, githubkit.rest.models.Runner):
# However, to make use of redis' search capability, we
# have to use Field(index=True), and there was some
# issue with the search when doing so.
# Until we figure out the issue, we will have to
# manually define the fields here.


class RunnerStatus(str, Enum):
    online = "online"
    idle = "idle"
    offline = "offline"


class RunnerLabel(PydanticBaseModel):
    """Self hosted runner label

    A label for a self hosted runner.
    """

    id: Optional[int] = None
    name: str = Field(description="Name of the label.", default=...)
    type: Optional[Literal["read-only", "custom"]] = "custom"


class Runner(BaseModel):
    name: str = Field(index=True, description="Runner name")
    runner_group_id: Optional[int] = Field(
        index=True, default=None, description="Runner group id"
    )
    backend_instance: Optional[str] = Field(
        index=True, description="Backend instance id", default=None
    )
    backend: Optional[str] = Field(index=True, description="Backend type")
    status: RunnerStatus = Field(
        default=RunnerStatus.offline, index=True, full_text_search=True
    )
    busy: bool
    labels: Optional[List[RunnerLabel]] = []
    created_at: Optional[datetime]
    updated_at: Optional[datetime]
