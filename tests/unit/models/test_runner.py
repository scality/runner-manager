import pytest
from hypothesis import given
from hypothesis import strategies as st
from redis_om import Migrator, NotFoundError

from runner_manager.models.runner import Runner


@given(st.builds(Runner))
def test_validate_runner(instance: Runner):
    assert instance.name is not None
    assert instance.status in ["online", "offline", "idle"]
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
