from typing import Dict, Iterable, List, Literal

from docker import DockerClient
from docker.errors import APIError, NotFound
from docker.models.containers import Container
from pydantic import Field
from redis_om import NotFoundError

from runner_manager.backend.base import BaseBackend
from runner_manager.models.backend import Backends, DockerConfig, DockerInstanceConfig, ContainerConfig
from runner_manager.models.runner import Runner


class DockerBackend(BaseBackend):
    name: Literal[Backends.docker] = Field(default=Backends.docker)

    config: DockerConfig
    instance_config: DockerInstanceConfig

    @property
    def client(self) -> DockerClient:
        """Returns a docker client."""
        return DockerClient(base_url=self.config.base_url)

    def create(self, runner: Runner):
        if self.manager:
            labels: Iterable[tuple[str, str]] = [
                ("runner-manager", self.manager),
            ]
            self.instance_config.labels.update(labels)
        config: ContainerConfig = self.instance_config.configure_instance(runner)
        container: Container = self.client.containers.run(
            config,
            name=runner.name,
            remove=self.instance_config.remove,
        )
        # container: Container = self.client.containers.run(
        #     self.instance_config.configure_instance(runner),
        #     name=runner.name,
        #     remove=self.instance_config.remove,
        # )

        # set container id as instance_id
        runner.instance_id = container.id

        return super().create(runner)

    def update(self, runner: Runner):
        """Update a runner instance.

        We cannot update a container, so we just gonna ensure the runner
        is running and is up to date.
        """
        container: Container = self.client.containers.get(runner.instance_id)
        if container.status != "running":
            raise Exception(f"Container {container.id} is not running.")
        return super().update(runner)

    def delete(self, runner: Runner):
        try:
            if runner.instance_id:
                container = self.client.containers.get(runner.instance_id)
            else:
                container = self.client.containers.get(runner.name)
            container.stop()
            container.remove(force=True)
        except NotFound:
            pass
        except APIError as e:
            if e.status_code == 409:
                # container is already stopped
                pass
            else:
                raise e
        return super().delete(runner)

    def get(self, instance_id: str) -> Runner:
        container = self.client.containers.get(instance_id)
        return Runner.find(Runner.instance_id == container.id).first()

    def list(self) -> List[Runner]:
        containers: List[Container] = self.client.containers.list(
            filters={"label": f"runner-manager={self.manager}"}
        )
        runners: List[Runner] = []
        for container in containers:
            try:
                runners.append(Runner.find(Runner.instance_id == container.id).first())
            except NotFoundError:
                runner: Runner = Runner(
                    name=container.name,
                    instance_id=container.id,
                    busy=False,
                )
                runner.save()
                runners.append(runner)
                continue

        return runners
