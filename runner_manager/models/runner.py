from datetime import datetime, timedelta
from enum import Enum
from typing import List, Literal, Optional

import redis
from githubkit.rest.models import Runner as GitHubRunner
from githubkit.rest.types import OrgsOrgActionsRunnersGenerateJitconfigPostBodyType
from githubkit.webhooks.types import WorkflowJobEvent
from pydantic import BaseModel as PydanticBaseModel
from redis_om import Field, NotFoundError

from runner_manager.clients.github import GitHub
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
    runner_group_name: str = Field(
        index=True,
        full_text_search=True,
        description="Runner group name",
        default="default",
    )
    instance_id: Optional[str] = Field(
        index=True,
        full_text_search=True,
        description="Backend instance id",
        default=None,
    )
    token: Optional[str] = None
    encoded_jit_config: Optional[str] = None
    backend: Optional[str] = Field(index=True, description="Backend type")
    status: RunnerStatus = Field(
        default=RunnerStatus.offline, index=True, full_text_search=True
    )
    busy: bool
    labels: List[RunnerLabel] = []
    organization: str = Field(default=None, index=True, description="Organization name")
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

    def time_to_start_expired(self, timeout: timedelta) -> bool:
        return self.is_offline and self.time_since_created > timeout

    def time_to_live_expired(self, time_to_live: timedelta) -> bool:
        return self.is_online and self.time_since_started > time_to_live

    def update_from_github(self, github: GitHub) -> "Runner":
        if self.id is not None:
            github_runner: GitHubRunner = (
                github.rest.actions.get_self_hosted_runner_for_org(
                    org=self.organization, runner_id=self.id
                ).parsed_data
            )
            self.status = RunnerStatus(self.status)
            self.busy = github_runner.busy
        log.info(f"Runner {self.name} status updated to {self.status}")
        return self.save()

    def generate_jit_config(self, github: GitHub) -> "Runner":
        """Generate JIT config for the runner"""
        assert self.organization is not None, "Organization name is required"
        assert self.runner_group_id is not None, "Runner group id is required"
        jitconfig = github.rest.actions.generate_runner_jitconfig_for_org(
            org=self.organization,
            data=OrgsOrgActionsRunnersGenerateJitconfigPostBodyType(
                name=self.name,
                runner_group_id=self.runner_group_id,
                labels=[label.name for label in self.labels],
            ),
        ).parsed_data
        self.id = jitconfig.runner.id
        self.encoded_jit_config = jitconfig.encoded_jit_config
        return self.save()

    def save(
        self,
        pipeline: Optional[redis.client.Pipeline] = None,
    ) -> "Runner":
        """Create a runner.

        Returns:
            Runner: Runner instance.
        """
        if self.created_at is None:
            self.created_at = datetime.now()
        return super().save(pipeline=pipeline)


Runner.update_forward_refs()
