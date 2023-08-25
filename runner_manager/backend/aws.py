from typing import Dict, List, Literal

from boto3 import client
from botocore.exceptions import ClientError
from mypy_boto3_ec2 import EC2Client
from pydantic import Field
from redis_om import NotFoundError

from runner_manager.backend.base import BaseBackend
from runner_manager.logging import log
from runner_manager.models.backend import AWSConfig, AWSInstanceConfig, Backends
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
        labels: Dict[str, str] = {}
        if self.manager:
            labels["runner-manager"] = self.manager
        self.instance_config.subnet_id = self.config.subnet_id
        instance_resource: Dict = self.instance_config.configure_instance(runner)
        try:
            instance = self.client.run_instances(**instance_resource)
            runner.instance_id = instance["Instances"][0]["InstanceId"]
            # Wait for instance to be running
            waiter = self.client.get_waiter("instance_running")
            waiter.wait(InstanceIds=[runner.instance_id])
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

    def list(self) -> List[Runner]:
        """List runners."""
        runners: List[Runner] = []
        try:
            reservations = self.client.describe_instances(
                Filters=[
                    {
                        "Name": "tag-key",
                        "Values": ["runner-manager"],
                    },
                    {
                        "Name": "instance-state-name",
                        "Values": ["running"],
                    },
                ]
            ).get("Reservations")
        except Exception as e:
            log.error(e)
            raise e
        for reservation in reservations:
            for instance in reservation.get("Instances", []):
                instance_id = instance.get("InstanceId", "")
                try:
                    runner = Runner.find(
                        Runner.instance_id == instance_id,
                    ).first()
                except NotFoundError:
                    runner = Runner(
                        name=instance_id,
                        instance_id=instance_id,
                        busy=False,
                    )
                runners.append(runner)
        return runners

    def update(self, runner: Runner) -> Runner:
        """Update a runner."""
        if runner.instance_id:
            try:
                self.client.create_tags(
                    Resources=[runner.instance_id],
                    Tags=[{"Key": "tag:status", "Value": runner.status}],
                )
            except Exception as e:
                log.error(e)
                raise e
        return super().update(runner)
