from enum import Enum

from pydantic import BaseModel


class BackendConfig(BaseModel):
    """Base class for backend configuration."""

    pass


class Backends(str, Enum):
    """Enum for backend types."""

    base = "base"
    docker = "docker"
    gcloud = "gcloud"
    aws = "aws"
