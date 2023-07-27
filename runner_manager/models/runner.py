from datetime import datetime
from enum import Enum
from typing import Optional

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


class Runner(BaseModel):
    name: str = Field(index=True)
    runner_group_id: int = Field(ge=0, index=True)
    instance_id: Optional[int] = Field(ge=0, index=True)
    status: RunnerStatus = Field(
        default=RunnerStatus.offline, index=True, full_text_search=True
    )
    busy: bool
    created_at: Optional[datetime]
    updated_at: Optional[datetime]
