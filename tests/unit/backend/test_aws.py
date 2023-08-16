import os
from typing import List

from pytest import fixture, mark, raises
from redis_om import NotFoundError

from runner_manager.backend.aws import AWSBackend
from runner_manager.models.backend import Backends, AWSConfig, AWSInstanceConfig
from runner_manager.models.runner import Runner
from runner_manager.models.runner_group import RunnerGroup

@fixture()
def aws_group(settings) -> RunnerGroup:
    config = AWSConfig()
    runner_group: RunnerGroup = RunnerGroup(
        id=2,
        name="test",
        organization="test",
        manager=settings.name,
        backend=AWSBackend(
            name=Backends.aws,
            config=config,
            instance_config=AWSInstanceConfig(),
        ),
        labels=[
            "label",
        ],
    )
    return runner_group

@fixture()
def aws_runner(runner: Runner, aws_group: RunnerGroup) -> Runner:
    # Cleanup and return a runner for testing
    aws_group.backend.delete(runner)
    return runner

def test_create_delete(aws_runner, aws_group):
    runner = aws_group.backend.create(aws_runner)
    assert runner.instance_id is not None
    assert runner.backend == "aws"
    assert Runner.find(Runner.instance_id == runner.instance_id).first() == runner
    aws_group.backend.delete(runner)
    with raises(NotFoundError):
        Runner.find(Runner.instance_id == runner.instance_id).first()
