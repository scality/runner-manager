from runner.Runner import Runner
from vm_creation.github_actions_api import (create_runner_token,
                                            force_delete_runner)
from vm_creation.openstack import create_vm, delete_vm
from runner.VmType import VmType


class RunnerManager(object):
    runner_counter: int
    github_organization: str
    runners: dict[str, Runner]
    runner_management: list[VmType]

    def __init__(self, org: str, config: list):
        self.runner_counter = 0
        self.github_organization = org
        self.runner_management = [VmType(elem) for elem in config]
        self.runners = {}

        for t in self.runner_management:
            for index in range(0, t.quantity):
                self.create_runner(t)

    def update_runner(self, github_runner: dict):
        runner = self.runners[github_runner['name']]

        if runner.action_id is None:
            runner.action_id = github_runner['id']

        if github_runner['status'] == 'offline' and runner.has_run and not runner.has_child:
            self.create_runner(runner.vm_type, parent=runner)
            runner.has_child = True

        if not runner.has_run and github_runner['status'] != 'offline':
            self.runner_started(runner)

    def filter_by_tags(self, tags: list[str]):
        pass

    def create_runner(self, vm_type: VmType, parent=None):
        name = self.next_runner_name()
        parent_name = parent.name if parent else None
        print(f'create runner: {name}')

        vm_id = create_vm(
            name=name,
            runner_token=create_runner_token(self.github_organization),
            vm_type=vm_type
        )
        self.runners[name] = Runner(name=name,
                                    vm_id=vm_id,
                                    vm_type=vm_type,
                                    parent_name=parent_name)
        self.runner_counter += 1

    def delete_runner(self, runner: Runner):
        if runner.action_id:
            force_delete_runner(self.github_organization, runner.action_id)

        if runner.vm_id:
            delete_vm(runner.vm_id)

        del self.runners[runner.name]

    def runner_started(self, runner: Runner):
        runner.has_run = True

        if runner.parent_name:
            self.delete_runner(self.runners[runner.parent_name])

    def next_runner_name(self):
        return f'{self.runner_counter}'

    def __del__(self):
        for runner in [elem for elem in self.runners.values()]:
            self.delete_runner(runner)
