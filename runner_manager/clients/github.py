"""

GitHub Client class for the runner manager.

Runner manager uses the GitHubkit library to interact with GitHub's API.
As the library was generated with the OpenAPI spec of the free license,
and the runner manager requires endpoints that are only available with
the Enterprise Cloud license, we have to manually define the
missing endpoints here.

"""


from datetime import datetime
from functools import cached_property
from typing import Dict, List, Literal, Optional

from githubkit import GitHub as GitHubKit
from githubkit.response import Response
from githubkit.rest import RestNamespace as RestNamespaceKit
from githubkit.rest.actions import ActionsClient as ActionsClientKit
from githubkit.rest.models import GitHubRestModel
from githubkit.utils import UNSET, Missing, exclude_unset
from githubkit.webhooks.models import GitHubWebhookModel
from pydantic import Field


class RunnerGroup(GitHubRestModel):
    id: Optional[int] = None
    name: str
    default: Optional[bool] = None
    runners_url: Optional[str] = None
    allows_public_repositories: Optional[bool] = None
    restricted_to_workflows: Optional[bool] = None
    selected_workflows: Optional[List[str]] = None
    workflow_restrictions_read_only: Optional[bool] = None
    selected_repository_ids: Optional[List[int]] = None
    runners: Optional[List[int]] = None


class OrgsOrgActionsRunnerGroupsGetResponse200(GitHubRestModel):
    total_count: int
    runner_groups: List[RunnerGroup]


# Missing methods from githubkit.webhooks.models
class WorkflowStepQueued(GitHubWebhookModel):
    """Workflow Step (Queued)"""

    name: str = Field(default=...)
    status: Literal["queued"] = Field(default=...)
    conclusion: None = Field(default=...)
    number: int = Field(default=...)
    started_at: datetime = Field(default=...)
    completed_at: None = Field(default=...)


class ActionsClient(ActionsClientKit):
    def get_self_hosted_runner_group_for_org(
        self,
        org: str,
        runner_group_id: int,
        *,
        headers: Optional[Dict[str, str]] = None,
    ) -> Response[RunnerGroup]:
        url = f"/orgs/{org}/actions/runner-groups/{runner_group_id}"

        headers = {"X-GitHub-Api-Version": self._REST_API_VERSION, **(headers or {})}

        return self._github.request(
            "GET",
            url,
            headers=exclude_unset(headers),
            response_model=RunnerGroup,
        )

    def list_self_hosted_runner_groups_for_org(
        self,
        org: str,
        per_page: Missing[int] = 30,
        page: Missing[int] = 1,
        *,
        headers: Optional[Dict[str, str]] = None,
    ) -> Response[OrgsOrgActionsRunnerGroupsGetResponse200]:
        url = f"/orgs/{org}/actions/runner-groups"

        params = {
            "per_page": per_page,
            "page": page,
        }
        headers = {"X-GitHub-Api-Version": self._REST_API_VERSION, **(headers or {})}

        return self._github.request(
            "GET",
            url,
            headers=exclude_unset(headers),
            params=exclude_unset(params),
            response_model=OrgsOrgActionsRunnerGroupsGetResponse200,
        )

    def create_self_hosted_runner_group_for_org(
        self,
        org: str,
        *,
        headers: Optional[Dict[str, str]] = None,
        data: Missing[RunnerGroup] = UNSET,
    ) -> Response[RunnerGroup]:
        url = f"/orgs/{org}/actions/runner-groups"

        json = data.dict(exclude_unset=True) if data else None

        headers = {"X-GitHub-Api-Version": self._REST_API_VERSION, **(headers or {})}

        return self._github.request(
            "POST",
            url,
            headers=exclude_unset(headers),
            json=json,
            response_model=RunnerGroup,
        )

    def delete_self_hosted_runner_group_from_org(
        self,
        org: str,
        runner_group_id: int,
        *,
        headers: Optional[Dict[str, str]] = None,
    ) -> Response:
        url = f"/orgs/{org}/actions/runner-groups/{runner_group_id}"

        headers = {"X-GitHub-Api-Version": self._REST_API_VERSION, **(headers or {})}

        return self._github.request(
            "DELETE",
            url,
            headers=exclude_unset(headers),
        )


class RestNamespace(RestNamespaceKit):
    @cached_property
    def actions(self) -> ActionsClient:
        return ActionsClient(self._github)


class GitHub(GitHubKit):
    @cached_property
    def rest(self) -> RestNamespace:
        return RestNamespace(self)
