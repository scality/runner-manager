from collections.abc import Callable


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
            for index in range(0, t.quantity['min']):
                self.create_runner(t)

    def update(self, github_runners: list[dict]):
        for elem in github_runners:
            runner = self.runners[elem['name']]
            runner.update_status(elem)

            if runner.action_id is None:
                runner.action_id = elem['id']

        for vm_type in self.runner_management:
            current_online = len(
                self.filter_runners(vm_type, lambda r: not r.has_run and r.action_id)
            )
            offlines = self.filter_runners(vm_type, lambda r: r.has_run)

            print(','.join([f"{elem.name} {elem.status}" for elem in self.filter_runners(vm_type)]))
            print(','.join([f"{elem.name} {elem.status}" for elem in offlines]))

            while self.need_new_runner(vm_type):
                self.create_runner(vm_type)

            if current_online > 0 and len(offlines) > 0:
                for elem in offlines:
                    self.delete_runner(elem)

    def need_new_runner(self, vm_type: VmType):
        current_online_or_creating = self.filter_runners(vm_type, lambda r: not r.has_run).__len__()
        current_running = self.filter_runners(vm_type, lambda r: r.status == 'running').__len__()

        return current_online_or_creating - current_running < vm_type.quantity['min'] and \
            current_online_or_creating < vm_type.quantity['max']

    def filter_runners(self, vm_type: VmType, cond: Callable[[Runner], bool] or None = None):
        if cond:
            return list(filter(
                lambda e: e.vm_type.tags == vm_type.tags and cond(e),
                self.runners.values()
            ))
        return list(filter(
            lambda e: e.vm_type.tags == vm_type.tags,
            self.runners.values()
        ))

    def create_runner(self, vm_type: VmType, parent=None):
        name = self.next_runner_name()
        parent_name = parent.name if parent else None

        vm_id = create_vm(
            name=name,
            runner_token=create_runner_token(self.github_organization),
            vm_type=vm_type
        )
        self.runners[name] = Runner(name=name,
                                    vm_id=vm_id,
                                    vm_type=vm_type,
                                    parent_name=parent_name)

    def delete_runner(self, runner: Runner):
        if runner.action_id:
            force_delete_runner(self.github_organization, runner.action_id)

        if runner.vm_id:
            delete_vm(runner.vm_id)

        del self.runners[runner.name]

    def next_runner_name(self):
        name = f'{self.runner_counter}'
        self.runner_counter += 1
        return name

    def __del__(self):
        for runner in [elem for elem in self.runners.values()]:
            self.delete_runner(runner)
