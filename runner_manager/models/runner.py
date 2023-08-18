from datetime import datetime, timedelta
from enum import Enum
from typing import List, Literal, Optional

from githubkit.rest.models import Runner as GitHubRunner
from githubkit.webhooks.types import WorkflowJobEvent
from pydantic import BaseModel as PydanticBaseModel
from redis_om import Field, NotFoundError

from runner_manager.logging import log
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
    id: Optional[int] = Field(index=True, default=None, description="Runner id")
    runner_group_id: Optional[int] = Field(
        index=True, default=None, description="Runner group id"
    )
    runner_group_name: Optional[str] = Field(
        index=True, full_text_search=True, description="Runner group name"
    )
    instance_id: Optional[str] = Field(
        index=True,
        full_text_search=True,
        description="Backend instance id",
        default=None,
    )
    token: Optional[str] = None
    backend: Optional[str] = Field(index=True, description="Backend type")
    status: RunnerStatus = Field(
        default=RunnerStatus.offline, index=True, full_text_search=True
    )
    busy: bool
    labels: Optional[List[RunnerLabel]] = []
    created_at: Optional[datetime]
    started_at: Optional[datetime]

    @classmethod
    def find_from_webhook(cls, webhook: WorkflowJobEvent) -> "Runner":
        """Find a runner from a webhook payload

        Args:
            webhook (WorkflowJobCompleted): A webhook payload
        Returns:
            Runner: A runner object
        """

        try:
            runner: Runner | None = cls.find(
                cls.id == webhook.workflow_job.runner_id
            ).first()
        except NotFoundError:
            runner = None
        return runner

    @property
    def is_online(self) -> bool:
        """Check if the runner is online

        Returns:
            bool: True if the runner is online, False otherwise.
        """
        return self.status == RunnerStatus.online

    @property
    def is_offline(self) -> bool:
        """Check if the runner is offline

        Returns:
            bool: True if the runner is offline, False otherwise.
        """
        return self.status == RunnerStatus.offline

    @property
    def is_idle(self) -> bool:
        """Check if the runner is idle

        Returns:
            bool: True if the runner is idle, False otherwise.
        """
        return self.status == RunnerStatus.idle

    @property
    def time_since_created(self) -> timedelta:
        """Time since the runner was created

        Returns:
            datetime: Time since the runner was created
        """
        if self.created_at:
            now = datetime.now()
            return now - self.created_at
        return timedelta()

    @property
    def time_since_started(self) -> timedelta:
        """Home long the runner has been running
        since last update

        Returns:
            datetime: Time since the runner was updated
        """
        if self.started_at:
            now = datetime.now()
            return now - self.started_at
        return timedelta()

    def time_to_start_expired(self, timeout: int) -> bool:
        return self.is_offline and self.time_since_created > timedelta(minutes=timeout)

    def time_to_live_expired(self, time_to_live: int) -> bool:
        return self.is_online and self.time_since_started > timedelta(
            minutes=time_to_live
        )

    def update_status(self, github_runner: GitHubRunner):
        self.status = RunnerStatus(github_runner.status)
        self.busy = github_runner.busy
        log.info(f"Runner {self.name} status updated to {self.status}")
        return self.save()


Runner.update_forward_refs()
