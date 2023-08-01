from enum import Enum


class Backends(str, Enum):
    base = "base"
    docker = "docker"
    gcloud = "gcloud"
    aws = "aws"
