from enum import Enum
from typing import Any, Dict, List, Literal, Optional

from google.cloud.compute import (
    AttachedDisk,
    AttachedDiskInitializeParams,
    ImagesClient,
    Instance,
)
from pydantic import BaseModel
from redis_om import Field


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

    instance: Any = None
    image: Any = None


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
    def __init__(
        self,
        gcp_config: GCPConfig,
        instance_name: str,
        image_family: str,
        image_project: str,
        machine_type: str,
        network: str,
        labels: Dict[str, str],
    ):
        super().__init__()  # Initialize the base class (InstanceConfig)
        # Create an Instance object (from google.cloud.compute)
        self.instance = Instance(name=instance_name)
        self.image = ImagesClient().get_from_family(
            project=image_project, family=image_family
        )
        # Set additional attributes specific to GCPInstanceConfig
        self.instance.disks.append(
            AttachedDisk(
                boot=True,
                auto_delete=True,
                initialize_params=AttachedDiskInitializeParams(
                    source_image=self.image.self_link,
                ),
            )
        )
        # Set additional attributes specific to GCPInstanceConfig
        self.instance.machine_type = (
            f"zones/{gcp_config.zone}/machineTypes/{machine_type}"
        )
        self.instance.network_interfaces = [
            {
                "network": f"projects/{gcp_config.project_id}/global/networks/{network}",
                "access_configs": [
                    {
                        "name": "External NAT",
                        "type_": "ONE_TO_ONE_NAT",
                    }
                ],
            }
        ]
        self.instance.labels = labels or {}
