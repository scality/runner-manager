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
        instance_resource: Dict = self.instance_config.configure_instance(runner)
        try:
            instance = self.client.run_instances(**instance_resource)
        except ClientError as e:
            raise e
        try:
            runner.instance_id = instance["Instances"][0]["InstanceId"]
        except Exception as e:
            raise e
        # Wait for instance to be running
        try:
            waiter = self.client.get_waiter("instance_running")
            waiter.wait(InstanceIds=[runner.instance_id])
        except Exception as e:
            raise e
        return super().create(runner)

    def delete(self, runner: Runner):
        """Delete a runner."""
        try:
            if runner.instance_id:
                self.client.terminate_instances(InstanceIds=[runner.instance_id])
        except ClientError as e:
            error = e.response.get("Error", {})
            if error.get("Code") == "InvalidInstanceID.NotFound":
                pass
            if error.get("Code") == "InvalidInstanceID.Malformed":
                log.error(f"Instance {runner.instance_id} malformed.")
                pass
            else:
                raise e
        return super().delete(runner)

    def get(self, instance_id: str) -> Runner:
        """Get a runner."""
        instance = {}
        try:
            instance = self.client.describe_instances(InstanceIds=[instance_id])
        except ClientError as e:
            error = e.response.get("Error", {})
            if error.get("Code") == "InvalidInstanceID.NotFound":
                log.error(f"Instance {instance_id} not found.")
            else:
                raise e
        try:
            reservations = instance.get("Reservations", [])
            if reservations:
                instances = reservations[0].get("Instances", [])
                if instances:
                    instance_id = instances[0]["InstanceId"]
                else:
                    raise ValueError(f"No instances found for {instance_id}")
            else:
                raise ValueError(f"No reservations found for {instance_id}")
        except Exception as e:
            raise e
        return Runner.find(Runner.instance_id == instance_id).first()

    def list(self) -> List[Runner]:
        """List runners."""
        runners: List[Runner] = []
        try:
            reservations = self.client.describe_instances(
                Filters=[
                    {
                        "Name": "tag:runner-manager",
                        "Values": ["aws"],
                    },
                    {
                        "Name": "instance-state-name",
                        "Values": ["running"],
                    },
                ]
            ).get("Reservations", [])
        except Exception as e:
            raise e
        for reservation in reservations:
            for instance in reservation.get("Instances", []):
                try:
                    runners.append(
                        Runner.find(
                            Runner.instance_id == instance.get("InstanceId", "")
                        ).first()
                    )
                except NotFoundError:
                    runner = Runner(
                        name=instance.get("InstanceId", ""),
                        instance_id=instance.get("InstanceId", ""),
                        busy=False,
                    )
                    runners.append(runner)
        return runners or []

    def update(self, runner: Runner) -> Runner:
        """Update a runner."""
        try:
            if runner.instance_id:
                self.client.describe_instances(
                    InstanceIds=[runner.instance_id],
                    Filters=[
                        {"Name": "instance-state-name", "Values": ["running"]},
                        {"Name": "tag:runner-manager", "Values": ["aws"]},
                    ],
                )
        except ClientError as e:
            error = e.response.get("Error", {})
            if error.get("Code") == "InvalidInstanceID.NotFound":
                log.error(f"Instance {runner.instance_id} not found.")
            else:
                raise e
        try:
            if runner.labels and runner.instance_id:
                self.client.create_tags(
                    Resources=[runner.instance_id],
                    Tags=[
                        {"Key": label.name, "Value": label.name}
                        for label in runner.labels
                    ],
                )
        except Exception as e:
            raise e
        return super().update(runner)
