import abc

from jinja2 import Environment
from jinja2 import FileSystemLoader
from marshmallow import Schema
from runners_manager.monitoring.prometheus import metrics
from runners_manager.runner.Runner import Runner


def create_vm_metric(func):
    def _decorator(self, *args, **kwargs):
        with metrics.runner_creation_time_seconds.labels(cloud=self.name).time():
            return func(self, *args, **kwargs)

    return _decorator


def delete_vm_metric(func):
    def _decorator(self, *args, **kwargs):
        with metrics.runner_delete_time_seconds.labels(cloud=self.name).time():
            return func(self, *args, **kwargs)

    return _decorator


class CloudManager(abc.ABC):
    CONFIG_SCHEMA: Schema = Schema
    CONFIG_VM_TYPE_SCHEMA: Schema = Schema
    name: str
    redhat_username: str
    redhat_password: str

    def __init__(
        self,
        name: str,
        settings: dict,
        redhat_username: str,
        redhat_password: str,
        ssh_keys: str,
    ):
        if self.CONFIG_SCHEMA:
            self.settings = self.CONFIG_SCHEMA().load(settings)
        self.name = name
        self.ssh_keys = ssh_keys
        self.redhat_username = redhat_username
        self.redhat_password = redhat_password

    @abc.abstractmethod
    def get_all_vms(self, prefix: str) -> list[Runner]:
        raise NotImplementedError

    @abc.abstractmethod
    @create_vm_metric
    def create_vm(
        self,
        runner: Runner,
        runner_token: int or None,
        github_organization: str,
        installer: str,
        call_number=0,
    ) -> int or None:
        raise NotImplementedError

    @abc.abstractmethod
    @delete_vm_metric
    def delete_vm(self, runner: Runner):
        raise NotImplementedError

    @abc.abstractmethod
    def delete_images_from_shelved(self, name):
        raise NotImplementedError

    @abc.abstractmethod
    def add_labels_to_instance(self, instance_name: str, labels_webhook: dict):
        raise NotImplementedError

    def script_init_runner(
        self, runner: Runner, token: int, github_organization: str, installer: str
    ):
        """
        Return the needed script by the virutal machines to run smoothly the Github runner
        It's generated by a jinja template
        """
        file_loader = FileSystemLoader("templates")
        env = Environment(loader=file_loader)
        env.trim_blocks = True
        env.lstrip_blocks = True
        env.rstrip_blocks = True

        template = env.get_template("init_runner_script.sh")
        output = template.render(
            installer=installer,
            github_organization=github_organization,
            token=token,
            name=runner.name,
            tags=",".join(runner.vm_type.tags),
            redhat_username=self.redhat_username,
            redhat_password=self.redhat_password,
            group="default",
            ssh_keys=self.ssh_keys,
        )
        return output
