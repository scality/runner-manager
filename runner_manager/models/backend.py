from enum import Enum
from pathlib import Path
from string import Template
from typing import Annotated, Dict, List, Optional

from google.cloud.compute import (
    AttachedDisk,
    Instance,
    Items,
    Metadata,
    NetworkInterface,
)
from pydantic import BaseModel, Field

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
    RUNNER_JIT_CONFIG: Optional[str] = None
    RUNNER_ORG: Optional[str] = None
    RUNNER_GROUP: Optional[str] = None


class InstanceConfig(BaseModel):
    """Base class for backend instance configuration."""

    startup_script: str = startup_sh.as_posix()

    def runner_env(self, runner: Runner) -> RunnerEnv:

        return RunnerEnv(
            RUNNER_NAME=runner.name,
            RUNNER_LABELS=",".join([label.name for label in runner.labels]),
            RUNNER_JIT_CONFIG=runner.encoded_jit_config,
            RUNNER_ORG=runner.organization,
            RUNNER_GROUP=runner.runner_group_name,
        )

    def template_startup(self, runner: Runner) -> str:
        """Template file with runner environment variables."""
        env: RunnerEnv = self.runner_env(runner)
        file = Path(self.startup_script)
        return Template(file.read_text()).safe_substitute(**env.dict())


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
    network: str = "global/networks/default"
    labels: Optional[Dict[str, str]] = {}
    image: Optional[str] = None
    disks: Optional[List[Annotated[dict, AttachedDisk]]] = []
    spot: bool = False

    disk_size_gb: int = 20

    network_interfaces: Optional[List[Annotated[dict, NetworkInterface]]] = []

    class Config:
        arbitrary_types_allowed = True

    def configure_metadata(self, runner: Runner) -> Metadata:
        items: List[Items] = []
        env: RunnerEnv = self.runner_env(runner)
        for key, value in env.dict().items():
            items.append(Items(key=key, value=value))
        # Template the startup script to install and setup the runner
        # with the appropriate configuration.
        startup_script = self.template_startup(runner)
        items.append(Items(key="startup-script", value=startup_script))
        return Metadata(items=items)

    def configure_instance(self, runner: Runner) -> Instance:
        """Configure instance."""
        metadata: Metadata = self.configure_metadata(runner)
        return Instance(
            name=runner.name,
            disks=self.disks,
            machine_type=self.machine_type,
            network_interfaces=self.network_interfaces,
            labels=self.labels,
            metadata=metadata,
        )


class AWSConfig(BackendConfig):
    """Configuration for AWS backend."""

    region: str = "us-west-2"
    subnet_id: str


class AWSInstanceConfig(InstanceConfig):
    """Configuration for AWS backend instance."""

    image: str = "ami-0735c191cf914754d"  # Ubuntu 22.04 for us-west-2
    instance_type: str = "t3.micro"
    subnet_id: Optional[str] = None
    security_group_ids: Optional[List[str]] = []
    max_count: int = 1
    min_count: int = 1
    user_data: Optional[str] = ""
    tags: Dict[str, str] = Field(default_factory=dict)
    volume_type: str = "gp3"
    disk_size_gb: int = 20

    class Config:
        arbitrary_types_allowed = True

    def configure_instance(self, runner: Runner) -> Dict:
        """Configure instance."""
        tags = {
            "Name": runner.name,
            "runner-manager": runner.manager,
        }
        tags.update(self.tags)
        block_device_mappings = [
            {
                "DeviceName": "/dev/sda1",
                "Ebs": {
                    "VolumeType": self.volume_type,
                    "VolumeSize": self.disk_size_gb,
                },
            }
        ]
        instance_config = {
            "ImageId": self.image,
            "InstanceType": self.instance_type,
            "SubnetId": self.subnet_id,
            "SecurityGroupIds": self.security_group_ids,
            "TagSpecifications": [
                {
                    "ResourceType": "instance",
                    "Tags": [
                        {"Key": key, "Value": value} for key, value in tags.items()
                    ],
                }
            ],
            "UserData": self.user_data,
            "MaxCount": self.max_count,
            "MinCount": self.min_count,
            "BlockDeviceMappings": block_device_mappings,
        }
        return instance_config
