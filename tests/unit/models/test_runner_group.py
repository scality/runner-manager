import pytest
from redis_om import Migrator, NotFoundError

from runner_manager.backend.base import BaseBackend
from runner_manager.models.runner import Runner
from runner_manager.models.runner_group import RunnerGroup


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


def test_create_runner_from_group(runner_group: RunnerGroup):
    runner_group.save()
    runner = runner_group.create_runner(Runner(name="test", busy=False))
    assert runner.runner_group_id == runner_group.id
    assert runner.labels == runner_group.runner_labels


def test_list_runners_from_group(runner_group: RunnerGroup):
    runner_group.save()
    runner = runner_group.create_runner(Runner(name="test", busy=False))
    assert runner in runner_group.get_runners()
