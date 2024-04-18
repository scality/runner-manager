from typing import List, Literal, Optional

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
        instance_resource: AwsInstance = self.instance_config.configure_instance(runner)
        try:
            instance = self.client.run_instances(**instance_resource)
            runner.instance_id = instance["Instances"][0]["InstanceId"]
        except Exception as e:
            log.error(e)
            raise e
        return super().create(runner)

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

    def _get_instance_name(self, instance: InstanceTypeDef) -> str:
        """Get the instance name."""
        name = ""
        for tag in instance.get("Tags", []):
            if tag.get("Key") == "Name":
                name = tag.get("Value", "")
        return name

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
                name = self._get_instance_name(instance)
                try:
                    runner = Runner.find(
                        Runner.instance_id == instance_id,
                    ).first()
                except NotFoundError:
                    runner = Runner(
                        name=name,
                        instance_id=instance_id,
                        runner_group_name=self.runner_group,
                        busy=False,
                        created_at=instance.get("LaunchTime"),
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
