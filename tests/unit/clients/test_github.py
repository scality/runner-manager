from typing import List

from githubkit import Response

from runner_manager.clients.github import RunnerGroup


def test_list_runner_groups(github, org):
    resp: Response = github.rest.actions.list_self_hosted_runner_groups_for_org(org=org)

    runner_groups: List[RunnerGroup] = resp.parsed_data.runner_groups
    for runner_group in runner_groups:
        runner_group: RunnerGroup


def test_create_runner_group(github, runner_group, org):
    resp: Response = github.rest.actions.create_self_hosted_runner_group_for_org(
        org=org, data=runner_group
    )

    group: RunnerGroup = resp.parsed_data
    assert group.name == runner_group.name


def test_get_runner_group(github, runner_group, org):
    resp: Response = github.rest.actions.get_self_hosted_runner_group_for_org(
        org=org, runner_group_id=runner_group.id
    )

    group: RunnerGroup = resp.parsed_data
    assert group.name == runner_group.name


def test_update_runner_group(github, runner_group, org):
    resp: Response = github.rest.actions.update_self_hosted_runner_group_for_org(
        org=org, runner_group_id=runner_group.id, data=runner_group
    )
    assert resp.status_code == 200


def test_delete_runner_group(github, runner_group, org):
    resp: Response = github.rest.actions.delete_self_hosted_runner_group_from_org(
        org=org, runner_group_id=runner_group.id
    )

    assert resp.status_code == 204
