from functools import lru_cache
from typing import List

from fastapi import APIRouter, Depends
from githubkit import Response
from githubkit.rest import OrgsOrgActionsRunnersGetResponse200, Runner
from pytest import fixture

from runner_manager.clients.github import GitHub
from runner_manager.dependencies import get_github, get_settings
from runner_manager.models.settings import Settings

router = APIRouter()


@router.get("/runners")
def list_runners(github: GitHub = Depends(get_github)) -> List[Runner]:
    resp: Response[
        List[OrgsOrgActionsRunnersGetResponse200]
    ] = github.rest.actions.list_self_hosted_runners_for_org(org="octo-org")

    return resp.parsed_data.runners


@lru_cache()
def settings():
    return Settings(
        github_token="test",
        github_base_url="http://localhost:4010",
    )


@fixture()
def github_app(fastapp):
    fastapp.dependency_overrides[get_settings] = settings
    return fastapp


def test_github_dependency(client, github_app):
    github_app.include_router(router)
    runners: List[Runner] = client.get("/runners").json()
    assert len(runners) >= 1
