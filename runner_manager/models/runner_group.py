import logging
import re
from datetime import datetime, timedelta, timezone
from typing import Any, List, Optional, Self, Union
from uuid import uuid4

import redis
from githubkit import Response
from githubkit.exception import RequestFailed
from githubkit.versions.latest.webhooks import WorkflowJobEvent
from pydantic import BaseModel as PydanticBaseModel
from pydantic import Field as PydanticField
from pydantic import root_validator, validator
from redis_om import Field, NotFoundError
from typing_extensions import Annotated

from runner_manager.backend.aws import AWSBackend
from runner_manager.backend.base import BaseBackend
from runner_manager.backend.docker import DockerBackend
from runner_manager.backend.gcloud import GCPBackend
from runner_manager.backend.vsphere import VsphereBackend
from runner_manager.clients.github import GitHub
from runner_manager.clients.github import RunnerGroup as GitHubRunnerGroup
from runner_manager.models.base import BaseModel
from runner_manager.models.runner import Runner, RunnerLabel, RunnerStatus

log = logging.getLogger(__name__)

regex = re.compile(r"[a-z](?:[-a-z0-9]{0,61}[a-z0-9])?|[1-9][0-9]{0,19}")


class BaseRunnerGroup(PydanticBaseModel):
    name: str
    organization: str
    repository: Optional[str] = None
    allows_public_repositories: Optional[bool] = True
    default: Optional[bool] = False
    runners_url: Optional[str] = None
    restricted_to_workflows: Optional[bool] = None
    selected_workflows: Optional[List[str]] = None
    workflow_restrictions_read_only: Optional[bool] = None
    selected_repository_ids: Optional[List[int]] = None
    runners: Optional[List[int]] = None
    max: Optional[int] = Field(ge=1, default=20)
    min: Optional[int] = Field(ge=0, default=0)
    os: str = Field(default="linux")
    arch: str = Field(default="x64")
    labels: List[str]
    job_started_script: Optional[str] = ""
    job_completed_script: Optional[str] = ""

    backend: Annotated[
        Union[BaseBackend, DockerBackend, GCPBackend, AWSBackend, VsphereBackend],
        PydanticField(..., discriminator="name"),
    ]


class RunnerGroup(BaseModel, BaseRunnerGroup):
    id: Optional[int] = Field(index=True, default=None)
    name: str = Field(index=True, full_text_search=True, max_length=39)
    organization: str = Field(index=True, full_text_search=True)
    repository: Optional[str] = Field(index=True, full_text_search=True)
    max: int = Field(index=True, ge=1, default=20)
    min: int = Field(index=True, ge=0, default=0)
    labels: List[str] = Field(index=True)
    queued: int = Field(default=0, ge=0)
    os: str = Field(default="linux")
    arch: str = Field(default="x64")
    job_started_script: Optional[str] = Field(default="")
    job_completed_script: Optional[str] = Field(default="")

    def __str__(self) -> str:
        return (
            f"{self.name} (max: {self.max}, min: {self.min}, "
            f"current: {len(self.get_runners())}, queued: {self.queued})"
        )

    @root_validator(skip_on_failure=True)
    def setup_backend(cls, values):
        values["backend"].manager = values["manager"]
        values["backend"].runner_group = values["name"]
        return values

    @validator("name")
    def validate_name(cls, v):
        """Validate group name.

        A group name must match the following regex:
        '[a-z](?:[-a-z0-9]{0,61}[a-z0-9])?|[1-9][0-9]{0,19}'.
        """
        assert regex.fullmatch(v), f"Group name {v} must be match of regex: {regex}"
        return v

    @property
    def runner_labels(self) -> List[RunnerLabel]:
        """Return self.labels as a list of RunnerLabel."""
        return [RunnerLabel(name=label) for label in self.labels]

    def generate_runner_name(self) -> str:
        """Generate a random runner name.

        Returns a string used as the runner name.
        - Prefixed by the group name.
        - Suffixed by a random uuid.
        - Match the following regex:
          '[a-z](?:[-a-z0-9]{0,61}[a-z0-9])?|[1-9][0-9]{0,19}'.
        - Must be unique and not already exist in the database.
        """

        name: str = f"{self.name}-{uuid4()}"
        return name

    def get_runners(self) -> List[Runner]:
        """Get the runners.

        Returns:
            List[Runner]: List of runners.
        """
        runners: List[Runner] = []
        try:
            runners = Runner.find(Runner.runner_group_name == self.name).all()
        except NotFoundError:
            pass
        return runners

    def download_url(self, github: GitHub) -> str:
        try:
            apps = github.rest.actions.list_runner_applications_for_org(
                org=self.organization
            ).parsed_data
            for app in apps:
                if app.os == self.os and app.architecture == self.arch:
                    return app.download_url
        except RequestFailed as e:
            log.error("Failed to retrieve runner applications")
            raise e
        raise Exception("No runner application found")

    def create_runner(self, github: GitHub) -> Runner | None:
        """Create a runner instance.

        Returns:
            Runner: Runner instance.
        """
        count = len(self.get_runners())
        if count < self.max and self.id:
            runner: Runner = Runner(
                name=self.generate_runner_name(),
                organization=self.organization,
                status=RunnerStatus.offline,
                busy=False,
                runner_group_id=self.id,
                created_at=datetime.now(timezone.utc),
                runner_group_name=self.name,
                labels=self.runner_labels,
                manager=self.manager,
                download_url=self.download_url(github),
                job_started_script=self.job_started_script,
                job_completed_script=self.job_completed_script,
            )
            runner.save()
            runner.generate_jit_config(github)
            if self.queued > 0:
                self.queued -= 1
                self.save()
            return self.backend.create(runner)
        else:
            self.queued += 1
            self.save()

    def update_runner(self: Self, webhook: WorkflowJobEvent) -> Runner:
        """Update a runner instance.

        Returns:
            Runner: Runner instance.
        """
        runner: Runner = Runner.find(
            Runner.name == webhook.workflow_job.runner_name
        ).first()
        runner.id = webhook.workflow_job.runner_id
        runner.status = RunnerStatus.online
        if isinstance(webhook.workflow_job.started_at, str):
            started_at = datetime.fromisoformat(webhook.workflow_job.started_at)
        else:
            started_at = webhook.workflow_job.started_at
        runner.started_at = started_at
        runner.busy = True
        runner.save()
        return self.backend.update(runner, webhook)

    def delete_runner(self, runner: Runner, github: GitHub) -> int:
        """Delete a runner instance.
        Start by checking if the runner still exists on GitHub,
        delete it if it does, then proceed to delete it from the backend.
        Returns:
            Runner: Runner instance.
        """
        if runner.id is not None:
            try:
                github.rest.actions.get_self_hosted_runner_for_org(
                    org=self.organization, runner_id=runner.id
                )
            except RequestFailed:
                log.info("Runner does not exist")
            else:
                github.rest.actions.delete_self_hosted_runner_from_org(
                    org=self.organization, runner_id=runner.id
                )
        return self.backend.delete(runner)

    def find_github_group(self, github: GitHub) -> GitHubRunnerGroup | None:
        """
        List the groups defined in GitHub and return a
        GitHubRunnerGroup instance if the group exists, None otherwise.

        A group is considered to exist if the name matches.
        """
        for group in github.paginate(
            github.rest.actions.list_self_hosted_runner_groups_for_org,
            map_func=lambda r: r.parsed_data.runner_groups,
            org=self.organization,
        ):
            group: GitHubRunnerGroup
            if group.name == self.name:
                return group

    @property
    def need_new_runner(self) -> bool:
        runners = self.get_runners()
        not_active = len([runner for runner in runners if runner.is_active is False])
        count = len(runners)
        return (not_active < self.min or self.queued > 0) and count < self.max

    @property
    def is_full(self) -> bool:
        """Return True if the max number of runners has been reached."""
        return len(self.get_runners()) >= self.max

    def create_github_group(self, github: GitHub) -> GitHubRunnerGroup:
        """Create a GitHub runner group."""

        if self.id is None:
            exists = self.find_github_group(github)
            self.id = exists.id if exists is not None else None

        group: Response[GitHubRunnerGroup]
        data = GitHubRunnerGroup(
            name=self.name,
            allows_public_repositories=self.allows_public_repositories,
        )
        if self.id is None:
            group = github.rest.actions.create_self_hosted_runner_group_for_org(
                org=self.organization, data=data
            )
        else:
            group = github.rest.actions.update_self_hosted_runner_group_for_org(
                org=self.organization, runner_group_id=self.id, data=data
            )
        return group.parsed_data

    def save(
        self,
        pipeline: Optional[redis.client.Pipeline] = None,
        github: Optional[GitHub] = None,
    ) -> "RunnerGroup":
        """Create a runner group.

        Args:
            github (GitHub): GitHub instance.

        Returns:
            RunnerGroup: Runner group instance.
        """
        # add label "self-hosted" to the list of labels
        if "self-hosted" not in self.labels:
            self.labels.append("self-hosted")
        if github:
            github_group: GitHubRunnerGroup = self.create_github_group(github)
            self.id = github_group.id
        return super().save(pipeline=pipeline)

    @classmethod
    def find_from_webhook(cls, webhook: WorkflowJobEvent) -> "RunnerGroup | None":
        """Find the runner group from a webhook instance.

        Args:
            webhook (WorkflowJobInProgress): Webhook instance.

        Returns:
            RunnerGroup: Runner group instance.
        """
        if webhook.workflow_job.runner_group_id is None:
            return None
        try:
            group: RunnerGroup | None = cls.find(
                (cls.id == webhook.workflow_job.runner_group_id)
            ).first()
        except NotFoundError:
            group = None
        return group

    @classmethod
    def find_from_labels(cls, labels: List[str]) -> "RunnerGroup":
        """Find the runner group from a list of labels.

        Args:
            labels (List[str]): List of labels.

        Returns:
            RunnerGroup: Runner group instance.
        """
        try:
            group: RunnerGroup | None = cls.find(
                *(cls.labels << label for label in labels)  # pyright: ignore
            ).first()
        except NotFoundError:
            group = None
        return group

    def healthcheck(
        self, time_to_live: timedelta, timeout_runner: timedelta, github: GitHub
    ):
        """Healthcheck runner group."""
        runners = self.get_runners()
        for runner in runners:
            runner.update_from_github(github)
            if runner.time_to_live_expired(time_to_live):
                self.delete_runner(runner, github)
            if runner.time_to_start_expired(timeout_runner):
                self.delete_runner(runner, github)
        while self.need_new_runner:
            runner: Runner = self.create_runner(github)
            if runner:
                log.info(f"Runner {runner.name} created")
        idle_runners = [runner for runner in self.get_runners() if runner.is_idle]
        # check if there's more idle runners than the minimum
        while len(idle_runners) > self.min:
            runner = idle_runners.pop()
            self.delete_runner(runner, github)
            log.info(f"Deleted idle {runner}")

    def reset(self, github: GitHub):
        """Reset runner group."""
        for runner in self.get_runners():
            if runner.id is not None:
                runner.update_from_github(github)
            if not runner.is_active:
                self.delete_runner(runner, github)
                self.create_runner(github)
                self.save()

    @classmethod
    def find_from_base(cls, basegroup: "BaseRunnerGroup") -> "RunnerGroup":
        """Find the runner group from a base instance.

        Args:
            group (BaseRunnerGroup): Base instance.

        Returns:
            RunnerGroup: Runner group instance.
        """
        try:
            group: RunnerGroup | None = cls.find(
                (cls.name == basegroup.name)
                & (cls.organization == basegroup.organization)
            ).first()
        except NotFoundError:
            group = None
        return group

    def delete_github_group(self, github: GitHub) -> Response[GitHubRunnerGroup] | None:
        """Delete a GitHub runner group."""
        if self.id:
            # check if runner group exists
            try:
                github.rest.actions.get_self_hosted_runner_group_for_org(
                    org=self.organization,
                    runner_group_id=self.id,
                )
            except RequestFailed:
                log.info("Runner group does not exist")
                return None
            return github.rest.actions.delete_self_hosted_runner_group_from_org(
                org=self.organization, runner_group_id=self.id
            )

        return None

    @classmethod
    def delete(
        cls,
        pk: Any,
        pipeline: Optional[redis.client.Pipeline] = None,
        github: Optional[GitHub] = None,
    ) -> int:
        """Delete a runner group.

        Proceeds in the following order:
        - Delete all runners.
        - Delete the runner group from GitHub. (if github is not None)
        - Delete the runner group from the database.

        Args:
            pk (Any): Runner group primary key.
            github (GitHub): GitHub instance.

        Returns: int
        """
        group: RunnerGroup = cls.get(pk)
        runners: List[Runner] = group.get_runners()
        if github:
            for runner in runners:
                group.delete_runner(runner, github)
            group.delete_github_group(github)
        db = cls._get_db(pipeline)

        return cls._delete(db, cls.make_primary_key(pk))


RunnerGroup.update_forward_refs()
