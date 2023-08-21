from enum import Enum
from typing import Dict, List, Optional

from google.cloud.compute import AttachedDisk, Instance, NetworkInterface
from pydantic import BaseModel

from runner_manager.models.runner import Runner


class Backends(str, Enum):
    """Enum for backend types."""

    base = "base"
    docker = "docker"
    gcloud = "gcloud"
    aws = "aws"


class BackendConfig(BaseModel):
    """Base class for backend configuration."""


class InstanceConfig(BaseModel):
    """Base class for backend instance configuration."""


class DockerInstanceConfig(InstanceConfig):
    """Configuration for Docker backend instance."""

    image: str = "runner:latest"

    # command to run, accept two types: str or List[str].
    command: Optional[List[str]] = []
    context: Optional[str] = None
    detach: bool = True
    remove: bool = False
    labels: Dict[str, str] = {}
    environment: Dict[str, str | None] = {
        "RUNNER_NAME": None,
        "RUNNER_LABELS": None,
        "RUNNER_TOKEN": None,
        "RUNNER_ORG": None,
        "RUNNER_GROUP": "default",
    }


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


class AWSConfig(BackendConfig):
    """Configuration for AWS backend."""

    region: str = "us-west-2"


class AWSInstanceConfig(InstanceConfig):
    """Configuration for AWS backend instance."""

    image: str = "ami-785db401"
    instance_type: str = "t2.micro"
    subnet_id: Optional[str] = None
    security_group_ids: Optional[List[str]] = None
    key_name: Optional[str] = None
    MaxCount: int = 1
    MinCount: int = 1
    tags: Dict[str, str] = {}
    user_data: Optional[str] = None
    block_device_mappings: Optional[List[Dict[str, str]]] = None

    class Config:
        arbitrary_types_allowed = True

    def configure_instance(self, runner: Runner) -> Dict:
        """Configure instance."""
        return {
            "ImageId": self.image,
            "InstanceType": self.instance_type,
            "SubnetId": self.subnet_id,
            "SecurityGroupIds": self.security_group_ids,
            "KeyName": self.key_name,
            "Tags": self.tags,
            "UserData": self.user_data,
            "MaxCount": self.MaxCount,
            "MinCount": self.MinCount,
            "BlockDeviceMappings": self.block_device_mappings,
        }
