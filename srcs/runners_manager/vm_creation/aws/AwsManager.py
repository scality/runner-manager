import logging
import boto3

import os

from runners_manager.monitoring.prometheus import metrics
from runners_manager.runner.Runner import Runner
from runners_manager.runner.Runner import VmType
from runners_manager.vm_creation.CloudManager import CloudManager
from runners_manager.vm_creation.CloudManager import create_vm_metric
from runners_manager.vm_creation.CloudManager import delete_vm_metric

from runners_manager.vm_creation.aws.schema import AwsConfig
from runners_manager.vm_creation.aws.schema import AwsConfigVmType

logger = logging.getLogger("runner_manager")

class AwsManager(CloudManager):
    CONFIG_SCHEMA = AwsConfig
    CONFIG_VM_TYPE_SCHEMA = AwsConfigVmType

    def __init__(
        self,
        name: str,
        settings: dict,
        redhat_username: str,
        redhat_password: str,
        ssh_keys: str,
    ):
        super(AwsManager, self).__init__(
            name, settings, redhat_username, redhat_password, ssh_keys
        )
        self.region = settings.get('config').get('region', os.environ.get('AWS_DEFAULT_REGION', 'us-west-2'))
        self.ec2 = boto3.client("ec2")
    
    def delete_existing_runner(self, runner: Runner):
        """Delete an old runner instance from AWS if it exists."""

        for reservation in self.ec2.describe_instances()['Reservations']:
            for instance in reservation['Instances']:
                for tag in instance.get('Tags', []):
                    if tag.get('Key') == 'Name' and tag.get('Value') == {runner.name}:
                        instance_id = instance.get('InstanceId')
                        return self.ec2.terminate_instances(InstanceIds=[instance_id])
                        
        logger.info(f"No existing instance for runner {runner.name} has been found")
        return None

    @create_vm_metric
    def create_vm(
        self,
        runner: Runner,
        runner_token: int or None,
        github_organization: str,
        installer: str,
        call_number=0,
    ):
        try:
            logger.info(f"Creating {runner.name} instance")

            user_data = self.script_init_runner(
                runner, runner_token, github_organization, installer
            )

            instance = self.ec2.run_instances(
                ImageId=runner.vm_type.config["image_id"],
                InstanceType=runner.vm_type.config["instance_type"],
                SecurityGroupIds=runner.vm_type.config["security_group_ids"],
                SubnetId=runner.vm_type.config["subnet_id"],
                MaxCount=1,
                MinCount=1,
                UserData=user_data,
                Placement={
                    'Region': self.region
                },
                BlockDeviceMappings=[
                    {
                        'DeviceName': '/dev/sda1',
                        'Ebs': {
                            'VolumeSize': int(runner.vm_type.config["disk_size_gb"]),
                            'DeleteOnTermination': True,
                            'VolumeType': 'gp2'
                        },
                    },
                ],
                TagSpecifications=[
                    {
                        'ResourceType': 'instance',
                        'Tags': [
                            {
                                'Key': 'Name',
                                'Value': runner.name
                            },
                            {
                                'Key': 'Runner-manager',
                                'Value': 'true'
                            }
                        ]
                    },
                ],
            )
            
            return instance['Instances'][0]['InstanceId']


        except Exception as exception:
            metrics.runner_creation_failed.labels(cloud=self.name).inc()
            logger.error(exception)
            raise exception

    @delete_vm_metric
    def delete_vm(self, runner):
        try:
            instances = self.ec2.describe_instances()

            for reservation in instances['Reservations']:
                for instance in reservation['Instances']:
                    for tag in instance.get('Tags', []):
                        if tag.get('Key') == 'Name' and tag.get('Value') == {runner.name}:
                            instance_id = instance.get('InstanceId')
                            self.ec2.terminate_instances(InstanceIds=[instance_id])
                            print(f"Instance with ID {instance_id} terminated.")
                            break
            logger.info(f"Instance of runner {runner.name} has been terminated")

        except Exception as exception:
            logger.info(f"Instance of runner {runner.name} {exception}")
            pass

    def get_all_vms(self, prefix: str) -> list[Runner]:
        # Get all vms in ec2
        instances = self.ec2.describe_instances()
        runners = []
        for instance in instances:
            for tag in instance.get('Tags', []):
                if tag.get('Key') == 'Name' and tag.get('Value').startswith(prefix):
                    runner = Runner(
                        tag.get('Value'),
                        instance.get('InstanceId'),
                        VmType(
                            {
                                "tags": [],
                                "config": {},
                                "quantity": {},
                            }
                        ),
                        self.name
                    )
                    runners.append(runner)
            return runners

    def delete_images_from_shelved(self, name):
        logger.info(f"nothing to do for {name}")