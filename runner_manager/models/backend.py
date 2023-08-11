from enum import Enum
from typing import Any, Dict, List, Literal, Optional

from google.cloud.compute import AttachedDisk, Instance, NetworkInterface
from pydantic import BaseModel
from redis_om import Field

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

    image: str

    # command to run, accept two types: str or List[str].
    command: Optional[List[str]] = []

    detach: bool = True
    remove: bool = False
    labels: Optional[Dict[str, str]] = {}
    environment: Optional[Dict[str, str]] = {}


class DockerConfig(BackendConfig):
    """Configuration for Docker backend."""

    base_url: str = "unix:///var/run/docker.sock"


class GCPConfig(BackendConfig):
    """Configuration for GCP backend."""

    project_id: str
    zone: str
    service_account_email: str = "default"


class GCPInstanceConfig(InstanceConfig):
    image_family: str
    image_project: str
    machine_type: str
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
