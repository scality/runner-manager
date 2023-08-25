import pytest
from githubkit.webhooks.models import WorkflowJobCompleted
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
    assert runner.runner_group_id == runner_group.id
    assert runner.labels == runner_group.runner_labels
    assert runner.id is not None
    assert runner.encoded_jit_config is not None


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
    assert RunnerGroup.find_from_labels(["notfound"]) is None


@given(webhook=WorkflowJobCompletedStrategy)
def test_find_from_webhook(runner_group: RunnerGroup, webhook: WorkflowJobCompleted):
    webhook.workflow_job.runner_group_id = runner_group.id
    runner_group.save()
    Migrator().run()
    assert RunnerGroup.find_from_webhook(webhook) == runner_group
    runner_group.delete(runner_group.pk)
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


def test_need_new_runner(runner_group: RunnerGroup, github: GitHub):
    runner_group.max = 2
    runner_group.min = 1
    runner_group.save()
    assert runner_group.need_new_runner is True
    runner = runner_group.create_runner(github)
    assert runner is not None
    # Set the runner as idle.
    runner.status = RunnerStatus.online
    runner.busy = False
    runner.save()
    Migrator().run()
    assert runner_group.need_new_runner is False
