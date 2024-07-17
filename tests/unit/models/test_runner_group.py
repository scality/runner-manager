from datetime import timezone

import pytest
from githubkit.versions.latest.models import (
    WebhookWorkflowJobCompleted as WorkflowJobCompleted,
)
from hypothesis import given
from pydantic import ValidationError
from redis_om import Migrator, NotFoundError

from runner_manager import Runner
from runner_manager.backend.base import BaseBackend
from runner_manager.clients.github import GitHub
from runner_manager.models.runner import RunnerStatus
from runner_manager.models.runner_group import BaseRunnerGroup, RunnerGroup

from ...strategies import WorkflowJobCompletedStrategy


def test_create_delete_runner_group(runner_group: RunnerGroup):
    runner_group.save()
    assert RunnerGroup.get(runner_group.pk) == runner_group
    RunnerGroup.delete(runner_group.pk)
    with pytest.raises(NotFoundError):
        RunnerGroup.get(runner_group.pk)


def test_find_runner_group(runner_group: RunnerGroup):
    runner_group.save()
    Migrator().run()
    assert runner_group.get(runner_group.pk) == runner_group
    print(RunnerGroup.find(RunnerGroup.name == runner_group.name).all())
    assert (
        RunnerGroup.find(RunnerGroup.name == runner_group.name).first() == runner_group
    )
    assert RunnerGroup.find().all() == [runner_group]

    RunnerGroup.delete(runner_group.pk)
    with pytest.raises(NotFoundError):
        RunnerGroup.find(RunnerGroup.name == runner_group.name).first()


def test_runner_group_backend(runner_group: RunnerGroup):
    runner_group.save()
    assert runner_group.backend.name == "base"
    assert isinstance(runner_group.backend, BaseBackend)
    assert isinstance(RunnerGroup.get(runner_group.pk).backend, BaseBackend)

    RunnerGroup.delete(runner_group.pk)


def test_create_runner_from_group(runner_group: RunnerGroup, github: GitHub):
    runner_group.save()
    runner = runner_group.create_runner(github)
    assert runner is not None
    assert runner.runner_group_id == runner_group.id
    assert runner.labels == runner_group.runner_labels
    assert runner.id is not None
    assert runner.encoded_jit_config is not None
    assert runner.created_at is not None
    assert runner.created_at.tzinfo == timezone.utc
    assert runner.job_started_script == ""
    assert runner.job_completed_script == ""


def test_list_runners_from_group(runner_group: RunnerGroup, github: GitHub):
    runner_group.save()
    runner = runner_group.create_runner(github)
    assert runner in runner_group.get_runners()


def test_find_runner_group_labels(runner_group: RunnerGroup):
    runner_group.labels = [
        "label",
        "label2",
        "label3",
    ]
    runner_group.save()
    assert RunnerGroup.find_from_labels(["label"]) == runner_group
    assert RunnerGroup.find_from_labels(["label", "label2"]) == runner_group
    assert RunnerGroup.find_from_labels(runner_group.labels) == runner_group


def test_applied_config_backend(runner_group: RunnerGroup):
    runner_group.save()
    assert runner_group.manager is not None
    assert runner_group.backend.manager == runner_group.manager
    assert runner_group.backend.runner_group == runner_group.name


def test_find_group_not_found(runner_group: RunnerGroup):
    runner_group.save()
    assert RunnerGroup.find_from_labels(["notfound"]) is None
    assert RunnerGroup.find_from_labels(["self-hosted", "notfound"]) is None
    assert RunnerGroup.find_from_labels(["label", "self-hosted", "notfound"]) is None


@given(webhook=WorkflowJobCompletedStrategy)
def test_find_from_webhook(runner_group: RunnerGroup, webhook: WorkflowJobCompleted):
    webhook.workflow_job.runner_group_id = runner_group.id
    runner_group.save()
    Migrator().run()
    assert RunnerGroup.find_from_webhook(webhook) == runner_group
    runner_group.delete(runner_group.pk)
    assert RunnerGroup.find_from_webhook(webhook) is None
    webhook.workflow_job.runner_group_name = None
    webhook.workflow_job.runner_group_id = None
    assert RunnerGroup.find_from_webhook(webhook) is None


def test_runner_group_delete_method(runner_group: RunnerGroup, github: GitHub):
    runner_group.id = None
    assert runner_group.default is False
    runner_group.save(github=github)
    assert runner_group.id is not None
    runner_group.default = True
    runner_group.save(github=github)
    assert runner_group.default is True
    runner: Runner = runner_group.create_runner(github)
    assert runner.runner_group_id == runner_group.id
    assert runner.runner_group_name == runner_group.name
    Migrator().run()
    assert runner in runner_group.get_runners()
    runner_group.delete(runner_group.pk, github=github)


def test_update_from_base(runner_group: RunnerGroup, github: GitHub):
    basegroup: BaseRunnerGroup = BaseRunnerGroup(
        name="basegroup",
        organization="test",
        labels=["test"],
        min=1,
        max=1,
        backend={"name": "base"},
    )
    runner_group.save(github=github)
    assert basegroup.name != runner_group.name
    runner_group.update(**basegroup.dict(exclude_unset=True))
    assert basegroup.name == runner_group.name


def test_runner_group_name():
    allowed_names = [
        "test",
        "test-42",
        "42",
        "a" * 39,
    ]
    forbidden_names = ["TEST", "test 42", "42-test", "a" * 40]
    for name in allowed_names:
        group = RunnerGroup(
            name=name,
            organization="test",
            backend={"name": "base"},
            labels=["test"],
        )
        assert group.name == name
    for name in forbidden_names:
        with pytest.raises(ValidationError):
            RunnerGroup(
                name=name,
                organization="test",
                backend={"name": "base"},
                labels=["test"],
            )

def test_job_scripts(runner_group: RunnerGroup, github: GitHub):
    runner_group.job_started_script = "Hello"
    runner_group.min = 1
    runner_group.save()
    runner = runner_group.create_runner(github)
    assert runner.job_completed_script == ""
    assert runner.job_started_script == runner_group.job_started_script


def test_need_new_runner(runner_group: RunnerGroup, github: GitHub):
    runner_group.max = 2
    runner_group.min = 1
    runner_group.save()
    assert runner_group.need_new_runner is True
    runner = runner_group.create_runner(github)
    # One runner is expected to be created we don't need a new one.
    assert runner_group.need_new_runner is False
    assert runner is not None
    # Pretend the runner is now active.
    runner.status = RunnerStatus.online
    runner.busy = True
    runner.save()
    Migrator().run()
    assert runner_group.need_new_runner is True


# test queue of runner_group
def test_runner_group_queue(runner_group: RunnerGroup, github: GitHub):
    runner_group.max = 2
    runner_group.min = 1
    runner_group.save()
    # Initially, we should need a new runner due to the min requirement
    assert runner_group.need_new_runner is True

    # Create a runner and simulate it being active (online and busy)
    runner = runner_group.create_runner(github)
    assert runner is not None
    assert runner_group.need_new_runner is False
    runner.status = RunnerStatus.online
    runner.busy = True
    runner.save()
    # Now, the runner is active (online and busy), and
    #  we haven't reached the min requirement,
    # so we still need a new runner
    assert runner_group.need_new_runner is True
    # Create a second runner, but it won't be added to the queue
    # since we haven't reached the max
    runner2 = runner_group.create_runner(github)
    assert runner2 is not None
    assert runner_group.need_new_runner is False
    # create a third runner so it goes to the queue
    runner3 = runner_group.create_runner(github)
    assert runner3 is None
    assert runner_group.queued == 1
    # Delete one of the active runners
    runner_group.backend.delete(runner)
    runner_group.save()
    # this reduces the total number of active runners
    # allowing the queued runner to be created
    assert runner_group.need_new_runner is True
    # create the queued runner
    runner4 = runner_group.create_runner(github)
    assert runner4 is not None
    assert runner_group.queued == 0


def test_find_github_group(runner_group: RunnerGroup, github: GitHub):
    runner_group.name = "octo-runner-group"
    exists = runner_group.find_github_group(github)
    assert exists is not None
    group = runner_group.save(github=github)
    assert exists.id == group.id


def test_is_full(runner_group: RunnerGroup, github: GitHub):
    runner_group.max = 2
    runner_group.min = 1
    runner_group.save()
    assert runner_group.is_full is False
    runner_group.create_runner(github)
    assert runner_group.is_full is False
    runner_group.create_runner(github)
    assert runner_group.is_full is True
