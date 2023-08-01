from datetime import datetime
from enum import Enum
from typing import Literal, Optional

from redis_om import Field

from runner_manager.models.base import BaseModel, EmbeddedBaseModel

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


class RunnerLabel(EmbeddedBaseModel):
    """Self hosted runner label

    A label for a self hosted runner
    """

    id: Optional[int] = Field(
        description="Unique identifier of the label.", default=None
    )
    name: str = Field(
        index=True, full_text_search=True, description="Name of the label.", default=...
    )
    type: Optional[Literal["read-only", "custom"]] = Field(
        description="The type of label. Read-only labels are applied automatically when the runner is configured.",
        default="custom",
    )


class Runner(BaseModel):
    name: str = Field(index=True)
    runner_group_id: int = Field(ge=0, index=True)
    backend_instance: Optional[int] = Field(ge=0, index=True)
    status: RunnerStatus = Field(
        default=RunnerStatus.offline, index=True, full_text_search=True
    )
    busy: bool
    labels: Optional[RunnerLabel] = Field(index=True, default=[])
    created_at: Optional[datetime]
    updated_at: Optional[datetime]
