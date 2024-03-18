import logging
from importlib.resources import files
from pathlib import Path
from typing import Dict, List, Literal, Optional

from docker import DockerClient
from docker.errors import APIError, NotFound
from docker.models.containers import Container
from githubkit.versions.latest.webhooks import WorkflowJobEvent
from pydantic import Field
from redis_om import NotFoundError

from runner_manager.backend.base import BaseBackend
from runner_manager.models.backend import Backends, DockerConfig, DockerInstanceConfig
from runner_manager.models.runner import Runner

log = logging.getLogger(__name__)


class DockerBackend(BaseBackend):
    name: Literal[Backends.docker] = Field(default=Backends.docker)

    config: DockerConfig = DockerConfig()
    instance_config: DockerInstanceConfig = DockerInstanceConfig()

    @property
    def client(self) -> DockerClient:
        """Returns a docker client."""
        return DockerClient(base_url=self.config.base_url)

    def _build(self, context: str, tag: str):
        """Simple build function to build a docker image.

        This function is meant to be used by tests to simplify the process of
        building a docker image for test environments.

        """
        path = Path(files("runner_manager").name)
        path = path.parent / context
        self.client.images.build(
            path=path.as_posix(),
            tag=tag,
            rm=True,
        )

    def _labels(self, runner: Runner) -> Dict[str, str | None]:
        """Return labels for the container."""
        labels: Dict[str, str | None] = {
            "group": runner.runner_group_name,
            "name": runner.name,
            "organization": runner.organization,
            "manager": self.manager,
        }
        labels.update(self.instance_config.labels)
        return labels

    def create(self, runner: Runner):
        if self.instance_config.context:
            self._build(self.instance_config.context, self.instance_config.image)

        labels = self._labels(runner)
        environment = self.instance_config.runner_env(runner).dict()
        log.info(f"Creating container for runner {runner.name}, labels: {labels}")
        container: Container = self.client.containers.run(
            self.instance_config.image,
            command=self.instance_config.command,
            detach=self.instance_config.detach,
            environment=environment,
            labels=labels,
            name=runner.name,
            remove=self.instance_config.remove,
        )
        runner.instance_id = container.id

        return super().create(runner)

    def update(self, runner: Runner, webhook: Optional[WorkflowJobEvent] = None):
        """Update a runner instance.

        We cannot update a container, so we just gonna ensure the runner
        is running and is up to date.
        """
        container: Container = self.client.containers.get(runner.instance_id)
        if container.status != "running":
            raise Exception(f"Container {container.id} is not running.")
        return super().update(runner, webhook)

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
            filters={"label": f"manager={self.manager}"}
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
