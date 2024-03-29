"""

GitHub Client class for the runner manager.

Runner manager uses the GitHubkit library to interact with GitHub's API.
As the library was generated with the OpenAPI spec of the free license,
and the runner manager requires endpoints that are only available with
the Enterprise Cloud license, we have to manually define the
missing endpoints here.

"""

from __future__ import annotations

from functools import cached_property
from typing import Dict, List, Optional

from githubkit import GitHub as GitHubKit
from githubkit.compat import GitHubModel as GitHubRestModel
from githubkit.response import Response
from githubkit.typing import Missing
from githubkit.utils import UNSET, exclude_unset
from githubkit.versions.v2022_11_28.rest import RestNamespace as RestNamespaceKit
from githubkit.versions.v2022_11_28.rest.actions import (
    ActionsClient as ActionsClientKit,
)


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
        )  # type: ignore

    def update_self_hosted_runner_group_for_org(
        self,
        org: str,
        runner_group_id: int,
        *,
        headers: Optional[Dict[str, str]] = None,
        data: Missing[RunnerGroup] = UNSET,
    ) -> Response[RunnerGroup]:
        url = f"/orgs/{org}/actions/runner-groups/{runner_group_id}"

        # exclude id from data
        json = (
            data.dict(exclude_unset=True, exclude={"id", "default"}) if data else None
        )

        headers = {"X-GitHub-Api-Version": self._REST_API_VERSION, **(headers or {})}

        return self._github.request(
            "PATCH",
            url,
            headers=exclude_unset(headers),
            json=json,
            response_model=RunnerGroup,
        )


class RestNamespace(RestNamespaceKit):
    @cached_property
    def actions(self) -> ActionsClient:
        return ActionsClient(self._github)


class GitHub(GitHubKit):
    @cached_property
    def rest(self) -> RestNamespace:
        return RestNamespace(self)
