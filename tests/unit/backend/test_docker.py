from typing import List

from docker.errors import NotFound
from pytest import fixture, raises
from redis_om import NotFoundError

from runner_manager.backend.docker import DockerBackend
from runner_manager.models.backend import Backends, DockerConfig, DockerInstanceConfig
from runner_manager.models.runner import Runner
from runner_manager.models.runner_group import RunnerGroup


@fixture()
def docker_group() -> RunnerGroup:
    runner_group: RunnerGroup = RunnerGroup(
        id=1,
        name="test",
        organization="test",
        backend=DockerBackend(
            name=Backends.docker,
            config=DockerConfig(),
            instance_config=DockerInstanceConfig(
                image="alpine:latest",
                command=["sleep", "infinity"],
            ),
        ),
        labels=[
            "label",
        ],
    )
    return runner_group


@fixture()
def docker_runner(runner: Runner, docker_group: RunnerGroup) -> Runner:
    docker_group.backend.delete(runner)
    return runner


def test_create_delete(docker_runner, docker_group):
    runner = docker_group.backend.create(docker_runner)
    assert runner.instance_id is not None
    assert runner.backend == "docker"
    assert Runner.find(Runner.instance_id == runner.instance_id).first() == runner
    docker_group.backend.delete(runner)
    with raises(NotFoundError):
        Runner.find(Runner.instance_id == runner.instance_id).first()


def test_update(docker_runner, docker_group):
    runner = docker_group.backend.create(docker_runner)
    docker_group.backend.update(runner)
    runner = Runner.find(Runner.instance_id == runner.instance_id).first()
    docker_group.backend.delete(runner)
    with raises(NotFound):
        docker_group.backend.get(runner.instance_id)


def test_list(docker_runner, docker_group):
    runner = docker_group.backend.create(docker_runner)
    assert runner in docker_group.backend.list()
    docker_group.backend.delete(runner)
    with raises(NotFound):
        docker_group.backend.get(runner.instance_id)


def test_list_manual_runner(docker_group: RunnerGroup):
    # test manually created runner and check if it is listed
    # within the database

    manual_runner: Runner = Runner(
        name="test-manual",
        busy=False,
    )
    # ensure container does not exist
    docker_group.backend.delete(manual_runner)

    docker_group.backend.client.containers.run(
        docker_group.backend.instance_config.image,
        remove=True,
        detach=True,
        labels={"runner-manager": docker_group.backend.runner_manager},
        command=docker_group.backend.instance_config.command,
        name="test-manual",
    )
    with raises(NotFoundError):
        Runner.find(Runner.name == manual_runner.name).first()
    runners: List[Runner] = docker_group.backend.list()
    manual_runner = Runner.find(Runner.name == manual_runner.name).first()

    assert manual_runner in runners
    docker_group.backend.delete(manual_runner)
