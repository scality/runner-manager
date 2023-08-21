from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional

from google.cloud.compute import (
    AttachedDisk,
    Instance,
    Items,
    Metadata,
    NetworkInterface,
)
from pydantic import BaseModel

from runner_manager.bin import startup_sh
from runner_manager.models.runner import Runner


class Backends(str, Enum):
    """Enum for backend types."""

    base = "base"
    docker = "docker"
    gcloud = "gcloud"
    aws = "aws"


class BackendConfig(BaseModel):
    """Base class for backend configuration."""


class RunnerEnv(BaseModel):
    """Base class for required runner instance environment variables."""

    RUNNER_NAME: Optional[str] = None
    RUNNER_LABELS: Optional[str] = None
    RUNNER_TOKEN: Optional[str] = None
    RUNNER_ORG: Optional[str] = None
    RUNNER_GROUP: Optional[str] = None


class InstanceConfig(BaseModel):
    """Base class for backend instance configuration."""

    def runner_env(self, runner: Runner) -> RunnerEnv:

        return RunnerEnv(
            RUNNER_NAME=runner.name,
            RUNNER_LABELS=", ".join([label.name for label in runner.labels]),
            RUNNER_TOKEN=runner.token,
            RUNNER_ORG=runner.organization,
            RUNNER_GROUP=runner.runner_group_name,
        )


class DockerInstanceConfig(InstanceConfig):
    """Configuration for Docker backend instance."""

    image: str = "runner:latest"

    # command to run, accept two types: str or List[str].
    command: Optional[List[str]] = []
    context: Optional[str] = None
    detach: bool = True
    remove: bool = False
    labels: Dict[str, str] = {}


class DockerConfig(BackendConfig):
    """Configuration for Docker backend."""

    base_url: str = "unix://var/run/docker.sock"


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
    startup_script: str = startup_sh.as_posix()
    network: str = "global/networks/default"
    labels: Optional[Dict[str, str]] = {}
    image: Optional[str] = None
    disks: Optional[List[AttachedDisk]] = None
    spot: bool = False
    network_interfaces: Optional[List[NetworkInterface]] = None

    class Config:
        arbitrary_types_allowed = True

    def runner_env(self, runner: Runner) -> List[Items]:
        items: List[Items] = []
        env: RunnerEnv = super().runner_env(runner)
        for key, value in env.dict().items():
            items.append(Items(key=key, value=value))
        # Adding startup script to install and configure runner
        startup_script = Path(self.startup_script).read_text()
        items.append(Items(key="startup-script", value=startup_script))
        return items

    def configure_instance(self, runner: Runner) -> Instance:
        """Configure instance."""
        items: List[Items] = self.runner_env(runner)
        return Instance(
            name=runner.name,
            disks=self.disks,
            machine_type=self.machine_type,
            network_interfaces=self.network_interfaces,
            labels=self.labels,
            metadata=Metadata(items=items),
        )
