from enum import Enum
from typing import Dict, List, Optional

from pydantic import BaseModel


class BackendConfig(BaseModel):
    """Base class for backend configuration."""

    pass


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


class Backends(str, Enum):
    """Enum for backend types."""

    base = "base"
    docker = "docker"
    gcloud = "gcloud"
    aws = "aws"


class DockerConfig(BackendConfig):
    """Configuration for Docker backend."""

    base_url: str = "unix:///var/run/docker.sock"
