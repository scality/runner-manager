from datetime import datetime, timezone

import pytest
from githubkit.webhooks.models import WorkflowJobCompleted
from hypothesis import given
from hypothesis import strategies as st
from redis_om import Migrator, NotFoundError

from runner_manager.clients.github import GitHub
from runner_manager.models.runner import Runner

from ...strategies import WorkflowJobCompletedStrategy


@given(st.builds(Runner))
def test_validate_runner(instance: Runner):
    assert instance.name is not None
    assert instance.status in ["online", "offline"]
    assert isinstance(instance.busy, bool)


def test_runner_create_delete(runner: Runner):
    runner.save()
    assert Runner.get(runner.pk) == runner
    Runner.delete(runner.pk)
    with pytest.raises(NotFoundError):
        Runner.get(runner.pk)


def test_find_runner(runner: Runner):
    runner.save()
    Migrator().run()
    runners = Runner.find().all()
    assert runner in runners

    assert runner == Runner.find(Runner.name == runner.name).first()
    assert (
        runner == Runner.find(Runner.runner_group_id == runner.runner_group_id).first()
    )
    assert runner == Runner.find(Runner.status == runner.status).first()
    Runner.delete(runner.pk)
    with pytest.raises(NotFoundError):
        Runner.find(Runner.name == runner.name).first()


@given(webhook=WorkflowJobCompletedStrategy)
def test_find_from_webhook(runner: Runner, webhook: WorkflowJobCompleted):
    webhook.workflow_job.runner_id = runner.id
    runner.save()
    assert Runner.find_from_webhook(webhook) == runner
    runner.delete(runner.pk)
    assert Runner.find_from_webhook(webhook) is None


def test_update_from_github(runner: Runner, github: GitHub):
    runner.save()
    assert runner.id is not None, "Runner must have an id"
    github_runner = github.rest.actions.get_self_hosted_runner_for_org(
        org=runner.organization, runner_id=runner.id
    ).parsed_data
    print(github_runner)
    runner.update_from_github(github)
    assert runner.busy == github_runner.busy
    assert runner.status == github_runner.status
    assert runner.status == "online"

    # Pretend the runner was deleted from github side
    # by forcing the mock server to return 404
    runner.update_from_github(github, headers={"Prefer": "code=404"})
    assert runner.status == "offline"
    assert runner.busy is False


def test_runner_timezone(runner: Runner):
    runner.started_at = datetime.now(timezone.utc)
    assert runner.created_at is not None
    assert runner.created_at.tzinfo == timezone.utc
    assert runner.started_at.tzinfo == timezone.utc
    assert runner.time_since_created > runner.time_since_started
