import logging
import boto3

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
        self.ec2 = boto3.client("ec2")
    
    def delete_existing_runner(self, runner: Runner):
        """Delete an old runner instance from AWS if it exists."""
        for instance in self.ec2.describe_instances()["Reservations"]:
            for i in instance["Instances"]:
                if i["InstanceId"] == runner.name:
                    logger.info(f"Found an existing instance of {runner.name}")
                    return self.delete_vm(i)
        logger.info(f"No existing instance for runner {runner.name} has been found")
        return None

    def configure_instance(
        self, runner, runner_token, github_organization, installer
    ):
        user_data = self.script_init_runner(
            runner, runner_token, github_organization, installer
        )

        image_id = 'ami-0735c191cf914754d' # Config
        instance_type = 't2.micro' # Config
        key_pair_name = 'gaspard_key' # Config
        security_group_ids = ['sg-0cf1e17cf459cfeff', 'sg-04a0f254a058a4c81']
        subnet_id = 'subnet-00c935cd1250d606f'

        instance = self.ec2.run_instances(
            ImageId=image_id,
            InstanceType=instance_type,
            KeyName=key_pair_name,
            SecurityGroupIds=security_group_ids,
            SubnetId=subnet_id,
            MaxCount=1,
            MinCount=1,
            UserData=user_data
        )

        return instance["Instances"][0]


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

            instance = self.configure_instance(
                runner, runner_token, github_organization, installer
            )
            instance_id = instance["InstanceId"]
            self.ec2.create_tags(
                Resources=[instance_id],
                Tags=[{"Key": "Name", "Value": runner.name}]
            )
            return instance_id

        except Exception as exception:
            metrics.runner_creation_failed.labels(cloud=self.name).inc()
            logger.error(exception)
            raise exception

    @delete_vm_metric
    def delete_vm(self, runner):
        try:
            self.ec2.terminate_instances(InstanceIds=[{runner.name}])
            logger.info(f"Instance of runner {runner.name} has been terminated")
        except Exception as exception:
            logger.info(f"Instance of runner {runner.name} {exception}")
            pass
