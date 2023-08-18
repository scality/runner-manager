from datetime import datetime
from typing import Any, List, Optional, Self, Union
from uuid import uuid4

import redis
from githubkit import Response
from githubkit.rest.models import AuthenticationToken
from githubkit.rest.models import Runner as GitHubRunner
from githubkit.webhooks.models import WorkflowJobInProgress
from githubkit.webhooks.types import WorkflowJobEvent
from pydantic import BaseModel as PydanticBaseModel
from pydantic import Field as PydanticField
from redis_om import Field, NotFoundError
from typing_extensions import Annotated

from runner_manager.backend.base import BaseBackend
from runner_manager.backend.docker import DockerBackend
from runner_manager.backend.gcloud import GCPBackend
from runner_manager.clients.github import GitHub
from runner_manager.clients.github import RunnerGroup as GitHubRunnerGroup
from runner_manager.logging import log
from runner_manager.models.base import BaseModel
from runner_manager.models.runner import Runner, RunnerLabel, RunnerStatus


class BaseRunnerGroup(PydanticBaseModel):
    name: str
    organization: str
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
        Union[BaseBackend, DockerBackend, GCPBackend],
        PydanticField(..., discriminator="name"),
    ]


class RunnerGroup(BaseModel, BaseRunnerGroup):

    id: Optional[int] = Field(index=True, default=None)
    name: str = Field(index=True, full_text_search=True)
    organization: str = Field(index=True, full_text_search=True)
    repository: Optional[str] = Field(index=True, full_text_search=True)
    max: Optional[int] = Field(index=True, ge=1, default=20)
    min: Optional[int] = Field(index=True, ge=0, default=0)
    labels: List[str] = Field(index=True)

    def __post_init_post_parse__(self):
        """Post init."""
        super().__post_init_post_parse__()
        if self.backend.manager is None:
            self.backend.manager = self.manager

    @property
    def runner_labels(self) -> List[RunnerLabel]:
        """Return self.labels as a list of RunnerLabel."""
        return [RunnerLabel(name=label) for label in self.labels]

    def generate_runner_name(self) -> str:
        """Generate a random runner name.

        Returns a string used as the runner name.
        - Prefixed by the group name.
        - Suffixed by a random uuid.
        - Limited by 63 characters.
        - Must be unique and not already exist in the database.
        """

        def _generate_name() -> str:
            """Generate a random name."""

            return f"{self.name}-{uuid4()}"

        name = _generate_name()
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

    def create_runner(self, token: AuthenticationToken) -> Runner | None:
        """Create a runner instance.

        Returns:
            Runner: Runner instance.
        """
        count = len(self.get_runners())
        if count < (self.max or 0):
            runner: Runner = Runner(
                name=self.generate_runner_name(),
                status=RunnerStatus.offline,
                token=token.token,
                busy=False,
                runner_group_id=self.id,
                created_at=datetime.now(),
                runner_group_name=self.name,
                labels=self.runner_labels,
                manager=self.manager,
            )
            runner.save()
            return self.backend.create(runner)
        return None

    def update_runner(self: Self, webhook: WorkflowJobInProgress) -> Runner:
        """Update a runner instance.

        Returns:
            Runner: Runner instance.
        """
        # return self.backend.update(runner)
        runner: Runner = Runner.find(
            Runner.name == webhook.workflow_job.runner_name
        ).first()
        runner.id = webhook.workflow_job.runner_id
        runner.status = RunnerStatus.online
        runner.busy = True
        runner.save()
        return self.backend.update(runner)

    def delete_runner(self, runner: Runner) -> int:
        """Delete a runner instance.

        Returns:
            Runner: Runner instance.
        """
        return self.backend.delete(runner)

    @property
    def need_new_runner(self) -> bool:
        return len(self.get_runners()) < (self.min or 0)

    def create_github_group(self, github: GitHub) -> GitHubRunnerGroup:
        """Create a GitHub runner group."""
        github_group: Response[
            GitHubRunnerGroup
        ] = github.rest.actions.create_self_hosted_runner_group_for_org(
            org=self.organization,
            data=GitHubRunnerGroup(
                name=self.name,
            ),
        )
        return github_group.parsed_data

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
        if github:
            github_group: GitHubRunnerGroup = self.create_github_group(github)
            self.id = github_group.id
        return super().save(pipeline=pipeline)

    @classmethod
    def find_from_webhook(cls, webhook: WorkflowJobEvent) -> "RunnerGroup":
        """Find the runner group from a webhook instance.

        Args:
            webhook (WorkflowJobInProgress): Webhook instance.

        Returns:
            RunnerGroup: Runner group instance.
        """
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
                (cls.labels << labels)  # pyright: ignore
            ).first()
        except NotFoundError:
            group = None
        return group

    def healthcheck(self, time_to_live: int, timeout_runner: int, github: GitHub):
        """Healthcheck runner group."""
        runners = self.get_runners()
        for runner in runners:

            if runner.id is not None:
                github_runner: GitHubRunner = (
                    github.rest.actions.get_self_hosted_runner_for_org(
                        self.organization, runner.id
                    ).parsed_data
                )
                runner = runner.update_status(github_runner)
            if runner.time_to_live_expired(time_to_live):
                self.delete_runner(runner)
            if runner.time_to_start_expired(timeout_runner):
                self.delete_runner(runner)
        while self.need_new_runner:
            token_response: Response[
                AuthenticationToken
            ] = github.rest.actions.create_registration_token_for_org(
                org=self.organization
            )
            token: AuthenticationToken = token_response.parsed_data
            runner: Runner = self.create_runner(token)
            if runner:
                log.info(f"Runner {runner.name} created")

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
        for runner in runners:
            group.delete_runner(runner)
        if github and group.id:
            github.rest.actions.delete_self_hosted_runner_group_from_org(
                org=group.organization, runner_group_id=group.id
            )
        db = cls._get_db(pipeline)

        return cls._delete(db, cls.make_primary_key(pk))


RunnerGroup.update_forward_refs()
