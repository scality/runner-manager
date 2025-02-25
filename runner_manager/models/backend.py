from enum import Enum
from pathlib import Path
from string import Template
from typing import Dict, List, Literal, NotRequired, Optional, Sequence, TypedDict

from mypy_boto3_ec2.literals import (
    InstanceMetadataTagsStateType,
    InstanceTypeType,
    VolumeTypeType,
)
from mypy_boto3_ec2.type_defs import (
    BlockDeviceMappingTypeDef,
    EbsBlockDeviceTypeDef,
    IamInstanceProfileTypeDef,
    InstanceMetadataOptionsRequestTypeDef,
    TagSpecificationTypeDef,
    TagTypeDef,
)
from pydantic import BaseModel, BaseSettings

from runner_manager.bin import startup_sh
from runner_manager.models.runner import Runner


class Backends(str, Enum):
    """Enum for backend types."""

    base = "base"
    docker = "docker"
    gcloud = "gcloud"
    aws = "aws"
    openstack = "openstack"
    vsphere = "vsphere"


class BackendConfig(BaseModel):
    """Base class for backend configuration."""


class RunnerEnv(BaseModel):
    """Base class for required runner instance environment variables."""

    RUNNER_NAME: Optional[str] = None
    RUNNER_LABELS: Optional[str] = None
    RUNNER_DOWNLOAD_URL: Optional[str] = None
    RUNNER_JIT_CONFIG: Optional[str] = None
    RUNNER_ORG: Optional[str] = None
    RUNNER_GROUP: Optional[str] = None
    RUNNER_REDHAT_USERNAME: Optional[str] = None
    RUNNER_REDHAT_PASSWORD: Optional[str] = None
    RUNNER_JOB_STARTED_SCRIPT: Optional[str] = ""
    RUNNER_JOB_COMPLETED_SCRIPT: Optional[str] = ""


class InstanceConfig(BaseSettings):
    """Base class for backend instance configuration."""

    startup_script: str = startup_sh.as_posix()
    redhat_username: Optional[str] = None
    redhat_password: Optional[str] = None

    def runner_env(self, runner: Runner) -> RunnerEnv:
        return RunnerEnv(
            RUNNER_NAME=runner.name,
            RUNNER_LABELS=",".join([label.name for label in runner.labels]),
            RUNNER_JIT_CONFIG=runner.encoded_jit_config,
            RUNNER_ORG=runner.organization,
            RUNNER_GROUP=runner.runner_group_name,
            RUNNER_DOWNLOAD_URL=runner.download_url,
            RUNNER_REDHAT_USERNAME=self.redhat_username,
            RUNNER_REDHAT_PASSWORD=(
                self.redhat_password if self.redhat_password else None
            ),
            RUNNER_JOB_STARTED_SCRIPT=runner.job_started_script,
            RUNNER_JOB_COMPLETED_SCRIPT=runner.job_completed_script,
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
    region: str = "europe-west1"
    service_account_email: str = "default"
    google_application_credentials: Optional[str] = None


class GCPInstanceConfig(InstanceConfig):
    image_family: str = "ubuntu-2004-lts"
    image_project: str = "ubuntu-os-cloud"
    image: Optional[str] = None
    machine_type: str = "e2-small"
    subnetwork: str = "default"
    enable_nested_virtualization: bool = True
    enable_external_ip: bool = True
    spot: bool = False
    disk_size_gb: int = 20
    disk_type: Literal["pd-ssd", "pd-standard"] = "pd-ssd"
    labels: Dict[str, str] = {}

    class Config:
        arbitrary_types_allowed = True


class AWSConfig(BackendConfig):
    """Configuration for AWS backend."""

    region: str = "us-west-2"


AwsSubnetListConfig = TypedDict(
    "AwsSubnetListConfig",
    {
        "subnet_id": str,
        "security_group_ids": NotRequired[Sequence[str]],
    },
)

AwsInstance = TypedDict(
    "AwsInstance",
    {
        "ImageId": str,
        "InstanceType": InstanceTypeType,
        "SubnetId": str,
        "SecurityGroupIds": Sequence[str],
        "TagSpecifications": Sequence[TagSpecificationTypeDef],
        "UserData": str,
        "BlockDeviceMappings": Sequence[BlockDeviceMappingTypeDef],
        "MaxCount": int,
        "MinCount": int,
        "IamInstanceProfile": IamInstanceProfileTypeDef,
        "MetadataOptions": InstanceMetadataOptionsRequestTypeDef,
    },
)


class AWSInstanceConfig(InstanceConfig):
    """Configuration for AWS backend instance."""

    image: str = "ami-0735c191cf914754d"  # Ubuntu 22.04 for us-west-2
    instance_type: InstanceTypeType = "t3.micro"
    subnet_id: str = ""
    security_group_ids: Sequence[str] = []
    max_count: int = 1
    min_count: int = 1
    user_data: Optional[str] = ""
    tags: Dict[str, str] = {}
    volume_type: VolumeTypeType = "gp3"
    disk_size_gb: int = 20
    iam_instance_profile_arn: str = ""
    instance_metadata_tags: InstanceMetadataTagsStateType = "disabled"
    subnet_configs: Sequence[AwsSubnetListConfig] = []

    def configure_instance(self, runner: Runner) -> AwsInstance:
        """Configure instance."""
        tags: Sequence[TagTypeDef] = [
            TagTypeDef(Key="Name", Value=runner.name),
            TagTypeDef(Key="manager", Value=runner.manager if runner.manager else ""),
            TagTypeDef(Key="runner_group", Value=runner.runner_group_name),
            TagTypeDef(Key="busy", Value=str(runner.busy)),
            TagTypeDef(Key="status", Value=runner.status),
        ]
        tags.extend(
            [TagTypeDef(Key=key, Value=value) for key, value in self.tags.items()]
        )
        user_data = self.template_startup(runner)

        block_device_mappings: Sequence[BlockDeviceMappingTypeDef] = [
            BlockDeviceMappingTypeDef(
                DeviceName="/dev/sda1",
                Ebs=EbsBlockDeviceTypeDef(
                    VolumeType=self.volume_type,
                    VolumeSize=self.disk_size_gb,
                    DeleteOnTermination=True,
                ),
            )
        ]
        tags_specification: Sequence[TagSpecificationTypeDef] = [
            TagSpecificationTypeDef(
                ResourceType="instance",
                Tags=tags,
            ),
            TagSpecificationTypeDef(
                ResourceType="volume",
                Tags=tags,
            ),
        ]
        iam_instance_profile: IamInstanceProfileTypeDef = IamInstanceProfileTypeDef(
            Arn=self.iam_instance_profile_arn
        )
        instance_metadata_options: InstanceMetadataOptionsRequestTypeDef = (
            InstanceMetadataOptionsRequestTypeDef(
                InstanceMetadataTags=self.instance_metadata_tags,
            )
        )
        return AwsInstance(
            ImageId=self.image,
            InstanceType=self.instance_type,
            SubnetId=self.subnet_id,
            SecurityGroupIds=self.security_group_ids,
            TagSpecifications=tags_specification,
            UserData=user_data,
            MaxCount=self.max_count,
            MinCount=self.min_count,
            BlockDeviceMappings=block_device_mappings,
            IamInstanceProfile=iam_instance_profile,
            MetadataOptions=instance_metadata_options,
        )


OpenstackInstance = TypedDict(
    "OpenstackInstance",
    {
        "name": str,
        "image": str,
        "flavor": str,
        "volume_size": int,
        "userdata": str,
        "meta": dict[str, str],
        "network": str,
    },
)


class OpenstackConfig(BackendConfig):
    cloud: Optional[str] = ""
    region_name: Optional[str] = ""


class OpenstackInstanceConfig(InstanceConfig):
    image: str = ""
    flavor: str = ""
    volume_size: int = 20
    network: str = ""
    meta: dict[str, str] = {}

    def configure_instance(self, runner: Runner) -> OpenstackInstance:
        """Configure Instance"""
        meta: dict[str, str] = {
            "Name": runner.name,
            "manager": runner.manager if runner.manager else "",
            "runner_group": runner.runner_group_name,
            "busy": str(runner.busy),
            "status": runner.status,
        }
        self.meta.update(meta)
        userdata = self.template_startup(runner)

        return OpenstackInstance(
            name=runner.name,
            image=self.image,
            flavor=self.flavor,
            network=self.network,
            volume_size=self.volume_size,
            userdata=userdata,
            meta=self.meta,
        )


class VsphereConfig(BackendConfig):
    """Configuration for vSphere backend."""

    server: str
    username: str
    password: str
    verify_ssl: bool = False


class VsphereInstanceConfig(InstanceConfig):
    """Configuration for vSphere backend instance."""

    disk_provisioning: Literal["thin", "thick"] = "thin"
    datacenter: str
    datastore: str
    library: str
    library_item: str
