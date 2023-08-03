from docker.errors import NotFound
from pytest import fixture, raises
from redis_om import NotFoundError

from runner_manager.backend.docker import DockerBackend
from runner_manager.models.backend import DockerConfig, DockerInstanceConfig
from runner_manager.models.runner import Runner


@fixture()
def docker_group(runner_group):
    runner_group.backend = "docker"
    runner_group.instance_config = DockerInstanceConfig(
        image="alpine:latest", command=["sleep", "infinity"]
    )
    return runner_group


@fixture()
def docker():
    config = DockerConfig()
    return DockerBackend(config=config)


@fixture()
def docker_runner(runner: Runner, docker: DockerBackend) -> Runner:
    try:
        container = docker.client.containers.get(runner.name)
        container.remove(force=True)
    except NotFound:
        pass
    return runner


def test_create_delete(docker, docker_runner, docker_group):
    runner = docker.create(docker_runner, docker_group.instance_config)
    assert runner.backend_instance is not None
    assert runner.backend == "docker"
    assert (
        Runner.find(Runner.backend_instance == runner.backend_instance).first()
        == runner
    )
    docker.delete(runner)
    with raises(NotFoundError):
        Runner.find(Runner.backend_instance == runner.backend_instance).first()


def test_update(docker, docker_runner, docker_group):
    runner = docker.create(docker_runner, docker_group.instance_config)
    docker.update(runner)
    runner = Runner.find(Runner.backend_instance == runner.backend_instance).first()
    docker.delete(runner)
    with raises(NotFound):
        docker.get(runner.backend_instance)


def test_list(docker, docker_runner, docker_group):
    runner = docker.create(docker_runner, docker_group.instance_config)
    assert runner in docker.list()
    docker.delete(runner)
    with raises(NotFound):
        docker.get(runner.backend_instance)
