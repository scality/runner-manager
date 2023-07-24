from redis_om import Field

from enum import Enum
from typing import Optional
from datetime import datetime
from runner_manager.models.base import BaseModel


class RunnerStatus(str, Enum):
    online = 'online'
    idle = 'idle'
    offline = 'offline'


class Runner(BaseModel):
    name: str = Field(index=True)
    runner_group_id: int = Field(ge=0, index=True)
    status: str = "offline"
    busy: bool
    created_at: Optional[datetime]
    updated_at: Optional[datetime]

    class Meta:
        model_key_prefix = __build_class__.__name__.lower()
