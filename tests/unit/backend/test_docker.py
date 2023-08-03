from docker.errors import NotFound
from pytest import fixture, raises
from redis_om import NotFoundError

from runner_manager.backend.docker import DockerBackend
from runner_manager.models.backend import DockerConfig, DockerInstanceConfig
from runner_manager.models.runner import Runner
from runner_manager.models.runner_group import RunnerGroup


@fixture()
def docker_group() -> RunnerGroup:
    runner_group = RunnerGroup(
        id=1,
        name="test",
        organization="test",
        backend=DockerBackend(
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
    try:
        container = docker_group.backend.client.containers.get(runner.name)
        container.remove(force=True)
    except NotFound:
        pass
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
