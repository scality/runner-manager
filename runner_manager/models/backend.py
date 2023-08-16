from enum import Enum
from typing import Dict, List, Literal, Optional, Iterable

from google.cloud.compute import AttachedDisk, Instance, NetworkInterface
from pydantic import BaseModel
from redis_om import Field
from docker.types.containers import ContainerConfig

from runner_manager.models.runner import Runner


class Backends(str, Enum):
    """Enum for backend types."""

    base = "base"
    docker = "docker"
    gcloud = "gcloud"
    aws = "aws"


class BackendConfig(BaseModel):
    """Base class for backend configuration."""

    name: Literal[Backends.base] = Field(
        index=True, full_text_search=True, default=Backends.base
    )


class InstanceConfig(BaseModel):
    """Base class for backend instance configuration."""


class DockerInstanceConfig(InstanceConfig):
    """Configuration for Docker backend instance."""

    image: str = "ghcr.io/actions/runner:latest"

    # command to run, accept two types: str or List[str].
    command: Optional[List[str]] = [
        "./config.sh",
        "--name",
        "${RUNNER_NAME}",
        "--labels",
        "${RUNNER_LABELS}",
        "--token",
        "${RUNNER_TOKEN}",
        "--url",
        "https://github.com/${RUNNER_ORG}/",
        "--runnergroup",
        "${RUNNER_GROUP}",
        "--unattended",
        "--ephemeral",
        "&&",
        "./run.sh"
    ]

    detach: bool = True
    remove: bool = False
    labels: Dict[str, str] = {}
    environment: Dict[str, str | None] = {
        'RUNNER_NAME': None,
        'RUNNER_LABELS': None,
        'RUNNER_TOKEN': None,
        'RUNNER_ORG': None,
        'RUNNER_REPO': None,
        'RUNNER_GROUP': 'default',
    }

    def configure_instance(self, runner: Runner) -> ContainerConfig:
        """Configure instance."""
        labels: Dict[str, str] = {
            "runner_group": runner.runner_group_name,
            "runner_name": runner.name,
            "organization": runner.organization,
        }
        labels.update(self.labels)
        self.environment['RUNNER_NAME'] = runner.name
        if runner.labels:
            self.environment['RUNNER_LABELS'] = ",".join(
                [label.name for label in runner.labels]
            )
        self.environment['RUNNER_TOKEN'] = runner.token
        self.environment['RUNNER_ORG'] = runner.organization
        self.environment['RUNNER_GROUP'] = runner.runner_group_name
        # TODO: Verify if this can be set
        # self.environment['RUNNER_REPO'] = runner.repo
        return ContainerConfig(
            version="3",
            image=self.image,
            command=self.command,
            labels=labels,
            environment=self.environment,
            detach=self.detach,
        )

class DockerConfig(BackendConfig):
    """Configuration for Docker backend."""

    base_url: str = "unix:///var/run/docker.sock"


class GCPConfig(BackendConfig):
    """Configuration for GCP backend."""

    project_id: str
    zone: str
    service_account_email: str = "default"
    google_application_credentials: Optional[str] = None


class GCPInstanceConfig(InstanceConfig):
    image_family: str = "ubuntu-2004-lts"
    image_project: str = "ubuntu-os-cloud"
    machine_type: str = "e2-small"
    network: str = "global/networks/default"
    labels: Optional[Dict[str, str]] = {}
    image: Optional[str] = None
    disks: Optional[List[AttachedDisk]] = None
    spot: bool = False
    network_interfaces: Optional[List[NetworkInterface]] = None

    class Config:
        arbitrary_types_allowed = True

    def configure_instance(self, runner: Runner) -> Instance:
        """Configure instance."""
        return Instance(
            name=runner.name,
            disks=self.disks,
            machine_type=self.machine_type,
            network_interfaces=self.network_interfaces,
            labels=self.labels,
        )
