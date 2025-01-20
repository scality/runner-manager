from copy import deepcopy
from random import shuffle
from typing import List, Literal, Optional, Sequence

from boto3 import client
from botocore.exceptions import ClientError
from githubkit.versions.latest.webhooks import WorkflowJobEvent
from mypy_boto3_ec2 import EC2Client
from mypy_boto3_ec2.type_defs import FilterTypeDef, InstanceTypeDef, TagTypeDef
from pydantic import Field
from redis_om import NotFoundError

from runner_manager.backend.base import BaseBackend
from runner_manager.logging import log
from runner_manager.models.backend import (
    AWSConfig,
    AwsInstance,
    AWSInstanceConfig,
    AwsSubnetListConfig,
    Backends,
)
from runner_manager.models.runner import Runner


class AWSBackend(BaseBackend):
    name: Literal[Backends.aws] = Field(default=Backends.aws)
    config: AWSConfig
    instance_config: AWSInstanceConfig

    @property
    def client(self) -> EC2Client:
        """Return a AWS Compute Engine client."""
        return client("ec2", region_name=self.config.region)

    def create(self, runner: Runner) -> Runner:
        """Create a runner."""
        if self.instance_config.subnet_id and self.instance_config.subnet_configs:
            raise Exception(
                "Instance config contains both subnet_id and subnet_configs, only one allowed."
            )
        if len(self.instance_config.subnet_configs) > 0:
            runner = self._create_from_subnet_config(
                runner, self.instance_config.subnet_configs
            )
            log.warn(f"Instance id: {runner.instance_id}")
        else:
            instance_resource: AwsInstance = self.instance_config.configure_instance(
                runner
            )
            try:
                runner = self._create(runner, instance_resource)
                log.warn(f"Instance id: {runner.instance_id}")
            except Exception as e:
                log.error(e)
                raise e
        return super().create(runner)

    def _create_from_subnet_config(
        self, runner: Runner, subnet_configs: Sequence[AwsSubnetListConfig]
    ) -> Runner:
        # Randomize the order of the Subnets - very coarse load balancing.
        # TODO: Skip subnets that have failed recently. Maybe with an increasing backoff.
        order = list(range(len(subnet_configs)))
        shuffle(order)
        subnet_config = self.instance_config.subnet_configs
        print(f"Order: {order}")
        for idx, i in enumerate(order):
            subnet_config = subnet_configs[i]
            try:
                # Copy the object to avoid modifying the object we were passed.
                count = self.instance_config.max_count - self.instance_config.min_count
                log.info(
                    f"Trying to launch {count} containers on subnet {subnet_config['subnet_id']}"
                )
                concrete_instance_config = deepcopy(self.instance_config)
                concrete_instance_config.subnet_id = subnet_config["subnet_id"]
                subnet_security_groups = subnet_config.get("security_group_ids", [])
                if subnet_security_groups:
                    security_groups = list(concrete_instance_config.security_group_ids)
                    security_groups += subnet_security_groups
                    concrete_instance_config.security_group_ids = security_groups
                instance_resource: AwsInstance = (
                    concrete_instance_config.configure_instance(runner)
                )
                return self._create(runner, instance_resource)
            except Exception as e:
                log.warn(
                    f"Creating instance in subnet {subnet_config['subnet_id']} failed with '{e}'. Retrying with another subnet."
                )
                if idx >= len(order) - 1:
                    raise e
        return runner

    def _create(self, runner: Runner, instance_resource: AwsInstance) -> Runner:
        instance = self.client.run_instances(**instance_resource)
        # Allow this to raise exception as we don't want to track an instance that
        # doesn't have an instance ID.
        runner.instance_id = instance["Instances"][0]["InstanceId"]  # type: ignore
        return runner

    def delete(self, runner: Runner):
        """Delete a runner."""
        if runner.instance_id:
            try:
                self.client.terminate_instances(InstanceIds=[runner.instance_id])
            except ClientError as e:
                error = e.response.get("Error", {})
                if error.get("Code") == "InvalidInstanceID.NotFound":
                    log.error(f"Instance {runner.instance_id} not found.")
                elif error.get("Code") == "InvalidInstanceID.Malformed":
                    log.error(f"Instance {runner.instance_id} malformed.")
                else:
                    raise e
        return super().delete(runner)

    def _get_tag_value(
        self, instance: InstanceTypeDef, key: str, default: str = ""
    ) -> str:
        """Get the tag value."""
        for tag in instance.get("Tags", []):
            if tag.get("Key") == key:
                return tag.get("Value", default)
        return default

    def list(self) -> List[Runner]:
        """List runners."""
        try:
            reservations = self.client.describe_instances(
                Filters=[
                    FilterTypeDef(Name="tag:manager", Values=[str(self.manager)]),
                    FilterTypeDef(
                        Name="tag:runner_group", Values=[str(self.runner_group)]
                    ),
                ]
            ).get("Reservations")
        except Exception as e:
            log.error(e)
            raise e
        runners: List[Runner] = []
        for reservation in reservations:
            for instance in reservation.get("Instances", []):
                instance_id = instance.get("InstanceId", "")
                name = self._get_tag_value(instance, "Name", instance_id)
                try:
                    runner = Runner.find(
                        Runner.instance_id == instance_id,
                    ).first()
                except NotFoundError:
                    runner = Runner(
                        name=name,
                        instance_id=instance_id,
                        runner_group_name=self.runner_group,
                        busy=bool(self._get_tag_value(instance, "busy")),
                        status=self._get_tag_value(instance, "status", "online"),
                        created_at=instance.get("LaunchTime"),
                        started_at=instance.get("LaunchTime"),
                    )
                runners.append(runner)
        return runners

    def update(
        self, runner: Runner, webhook: Optional[WorkflowJobEvent] = None
    ) -> Runner:
        """Update a runner."""
        if runner.instance_id:
            try:
                self.client.create_tags(
                    Resources=[runner.instance_id],
                    Tags=[
                        TagTypeDef(Key="status", Value=runner.status),
                        TagTypeDef(Key="busy", Value=str(runner.busy)),
                    ],
                )
            except Exception as e:
                log.error(e)
                raise e
        return super().update(runner, webhook)
