import os
from typing import Dict

from pytest import fixture, mark, raises
from redis_om import NotFoundError

from runner_manager.backend.aws import AWSBackend
from runner_manager.models.backend import AWSConfig, AWSInstanceConfig, Backends
from runner_manager.models.runner import Runner, RunnerLabel
from runner_manager.models.runner_group import RunnerGroup


@fixture()
def aws_group(settings) -> RunnerGroup:
    config = AWSConfig(subnet_id=os.getenv("AWS_SUBNET_ID", ""))
    runner_group: RunnerGroup = RunnerGroup(
        id=3,
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


def test_aws_instance_config(runner: Runner):
    config = AWSConfig(subnet_id="i-0f9b0a3b7b3b3b3b3")
    instance_config = AWSInstanceConfig(tags={"test": "test"})
    instance_config.subnet_id = config.subnet_id
    instance_resource: Dict = instance_config.configure_instance(runner)
    assert instance_resource["SubnetId"] == config.subnet_id
    assert {"Key": "test", "Value": "test"} in instance_resource["TagSpecifications"][
        0
    ]["Tags"]


@mark.skipif(not os.getenv("AWS_ACCESS_KEY_ID"), reason="AWS credentials not found")
def test_create_delete(aws_runner, aws_group):
    runner = aws_group.backend.create(aws_runner)
    assert runner.instance_id is not None
    assert runner.backend == "aws"
    assert Runner.find(Runner.instance_id == runner.instance_id).first() == runner
    aws_group.backend.delete(runner)
    with raises(NotFoundError):
        Runner.find(Runner.instance_id == runner.instance_id).first()


@mark.skipif(not os.getenv("AWS_ACCESS_KEY_ID"), reason="AWS credentials not found")
def test_list(aws_runner, aws_group):
    runner = aws_group.backend.create(aws_runner)
    assert runner in aws_group.backend.list()
    aws_group.backend.delete(runner)
    with raises(NotFoundError):
        aws_group.backend.get(runner.instance_id)


@mark.skipif(not os.getenv("AWS_ACCESS_KEY_ID"), reason="AWS credentials not found")
def test_update(aws_runner, aws_group):
    runner = aws_group.backend.create(aws_runner)
    runner.labels = [RunnerLabel(name="test", type="custom")]
    aws_group.backend.update(runner)
    assert runner.labels == [RunnerLabel(name="test", type="custom")]
    aws_group.backend.delete(runner)
    with raises(NotFoundError):
        aws_group.backend.get(runner.instance_id)
