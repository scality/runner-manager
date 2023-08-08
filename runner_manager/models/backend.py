from enum import Enum
from typing import Dict, List, Literal, Optional

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

    pass


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


class GCPInstanceConfig(InstanceConfig):
    """Configuration for GCP backend instance."""
    project_id: str
    zone: str
    machine_type: str
    image_family: str
    network: str
    subnet: str


class GCPConfig(BackendConfig):
    """Configuration for GCP backend."""

    project_id: str
    credentials_path: str
    region: str
    service_account_email: str
