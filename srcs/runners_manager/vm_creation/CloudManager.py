import abc
from runners_manager.runner.Runner import Runner


class CloudManager(abc.ABC):
    @abc.abstractmethod
    def __init__(self, settings: dict,
                 redhat_username: str, redhat_password: str,
                 ssh_keys: str):
        raise NotImplementedError

    @abc.abstractmethod
    def get_all_vms(self, organization: str) -> [str]:
        raise NotImplementedError

    @abc.abstractmethod
    def create_vm(self, runner: Runner, runner_token: int or None,
                  github_organization: str, installer: str, call_number=0):
        raise NotImplementedError

    @abc.abstractmethod
    def delete_vm(self, vm_id: str, image_name=None):
        raise NotImplementedError

    @abc.abstractmethod
    def delete_images_from_shelved(self, name):
        raise NotImplementedError
