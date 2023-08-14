import time
from typing import Dict, List, Literal

import boto3
from pydantic import Field

from runner_manager.backend.base import BaseBackend
from runner_manager.models.backend import AWSConfig, AWSInstanceConfig, Backends
from runner_manager.models.runner import Runner

class AWSBackend(BaseBackend):
    name: Literal[Backends.aws] = Field(default=Backends.aws)
    config: AWSConfig
    instance_config: AWSInstanceConfig

    @property
    def client(self) -> boto3.client:
        """Returns a AWS Compute Engine client."""
        return boto3.client('ec2', region_name=self.config.region)
    
    def create(self, runner: Runner) -> Runner:
        """Create a runner."""
                labels: Dict[str, str] = {}
        if self.manager:
            labels["runner-manager"] = self.manager
        instance_resource: Dict = self.instance_config.configure_instance()
        try:
            instance = self.client.run_instances(**instance_resource)
            runner.instance_id = instance["Instances"][0]["InstanceId"]
        except Exception as e:
            raise e
        return super().create(runner)
    
    def delete(self, runner: Runner) -> Runner:
        """Delete a runner."""
        try:
            instance = self.client.terminate_instances(InstanceIds=[runner.instance_id])
        except Exception as e:
            raise e
        return super().delete(runner)
    def get(self, intance_id: str) -> Runner:
        """Get a runner."""
        try:
            instance = self.client.describe_instances(InstanceIds=[runner.instance_id])
            instance_id = instance["Instances"][0]["InstanceId"]
        except Exception as e:
            raise e
        return Runner.find(Runner.instance_id == instance_id).first()
    def list(self) -> List[Runner]:
        """List runners."""
        runners: List[Runner] = []
        try:
            instances = self.client.describe_instances()
            for instance in instances["Reservations"]:
                for i in instance["Instances"]:
                    labels = i["Tags"]
                    if self.manager and "runner-manager" in labels:
                        runner = Runner(
                            name=i["InstanceId"],
                            instance_id=i["InstanceId"],
                            busy=False
                        )
                        runners.append(runner)
        except Exception as e:
            raise e
        return runners
    

