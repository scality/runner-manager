from typing import List

from fastapi import APIRouter, Depends
from githubkit import Response
from githubkit.rest import OrgsOrgActionsRunnersGetResponse200, Runner

from runner_manager.clients.github import GitHub
from runner_manager.dependencies import get_github

router = APIRouter()


@router.get("/runners")
def list_runners(github: GitHub = Depends(get_github)) -> List[Runner]:
    resp: Response[
        List[OrgsOrgActionsRunnersGetResponse200]
    ] = github.rest.actions.list_self_hosted_runners_for_org(org="octo-org")

    return resp.parsed_data.runners


def test_github_dependency(client, fastapp):
    fastapp.include_router(router, prefix="/api")
    # fastapp.dependency_overrides[get_settings] = settings
    runners: List[Runner] = client.get("/runners").json()
    assert len(runners) >= 1
