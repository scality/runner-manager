from typing import Dict, List

from docker import DockerClient
from docker.models.containers import Container
from pydantic import Field
from redis_om import NotFoundError

from runner_manager.models.backend import DockerConfig, DockerInstanceConfig
from runner_manager.models.runner import Runner

from .base import Backends, BaseBackend


class DockerBackend(BaseBackend):
    config: DockerConfig

    name: Backends = Field(Backends.docker, const=True)

    @property
    def client(self) -> DockerClient:
        """Returns a docker client."""
        return DockerClient(base_url=self.config.base_url)

    def create(self, runner: Runner, instance_config: DockerInstanceConfig):
        # TODO: Review model configuration and base method inputs

        # TODO: Retrieve value for runner-manager from settings.name
        labels: Dict[str, str] = {
            "runner-manager": "runner-manager",
        }
        if instance_config.labels:
            labels.update(instance_config.labels.items())

        container: Container = self.client.containers.run(
            instance_config.image,
            labels=labels,
            remove=instance_config.remove,
            detach=instance_config.detach,
            environment=instance_config.environment,
            command=instance_config.command,
            name=runner.name,
        )

        # set container id as backend_instance
        runner.backend_instance = container.id

        return super().create(runner)

    def update(self, runner: Runner):
        """Update a runner instance.

        We cannot update a container, so we just gonna ensure the runner
        is running and is up to date.
        """
        container: Container = self.client.containers.get(runner.backend_instance)
        if container.status != "running":
            raise Exception(f"Container {container.id} is not running.")
        return super().update(runner)

    def delete(self, runner: Runner):
        if runner.backend_instance:
            container = self.client.containers.get(runner.backend_instance)
        else:
            container = self.client.containers.get(runner.name)
        container.stop()
        container.remove()
        return super().delete(runner)

    def get(self, instance_id: str) -> Runner:
        container = self.client.containers.get(instance_id)
        return Runner.find(Runner.backend_instance == container.id).first()

    def list(self) -> List[Runner]:
        containers: List[Container] = self.client.containers.list(
            filters={"label": "runner-manager=runner-manager"}
        )
        runners: List[Runner] = []
        for container in containers:
            try:
                runners.append(
                    Runner.find(Runner.backend_instance == container.id).first()
                )
            except NotFoundError:
                runner: Runner = Runner(
                    name=container.name,
                    backend_instance=container.id,
                    status=container.labels["status"],
                    busy=container.labels["busy"],
                )
                runner.save()
                runners.append(runner)
                continue

        return runners
