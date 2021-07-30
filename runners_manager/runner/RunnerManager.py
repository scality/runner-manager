import logging
from collections.abc import Callable


from runners_manager.runner.Runner import Runner
from runners_manager.runner.RunnerFactory import RunnerFactory
from runners_manager.runner.VmType import VmType

logger = logging.getLogger("runner_manager")


class RunnerManager(object):
    vm_type: VmType
    runners: dict[str, Runner]
    factory: RunnerFactory

    def __init__(self, vm_type: VmType, factory: RunnerFactory):
        self.vm_type = vm_type
        self.factory = factory
        self.runners = {}

        for index in range(0, self.vm_type.quantity['min']):
            r = self.factory.create_runner(self.vm_type)
            self.runners[r.name] = r

    def update(self, github_runners: list[dict]):
        # Update status of each runner
        for elem in github_runners:
            runner = self.runners[elem['name']]
            runner.update_status(elem)

            if runner.action_id is None:
                runner.action_id = elem['id']

    def create_runner(self):
        r = self.factory.create_runner(self.vm_type)
        self.runners[r.name] = r

    def delete_runner(self, runner):
        self.factory.delete_runner(runner)
        del self.runners[runner.name]

    def respawn_runner(self, runner: Runner):
        self.factory.respawn_replace(runner)

    def too_much_runner(self):
        current_online = len(
            self.filter_runners(lambda r: r.action_id and r.status == 'online')
        )
        return current_online > self.vm_type.quantity['min']

    def need_new_runner(self):
        """
        This function define if we need new runners or not.
        This logic is based on the statement: They should be always x runner waiting,
            when x is the `min` variable set in the config file
        :param vm_type: Type of runner
        :return: True if can and need a new runner
        """
        current_online_or_creating = len(
            self.filter_runners(lambda r: not r.has_run and not r.status == 'running')
        )
        current_running = len(self.filter_runners(lambda r: r.status == 'running'))

        return current_online_or_creating < self.vm_type.quantity['min'] and \
               current_running + current_online_or_creating < self.vm_type.quantity['max']

    def filter_runners(self, cond: Callable[[Runner], bool]):
        return list(filter(
            lambda e: e.vm_type.tags == self.vm_type.tags and cond(e),
            self.runners.values()
        ))

    def __del__(self):
        """
        Here we delete the runners currently in the manager
        TODO Remove this function when we have a persistent database
        :return:
        """
        for runner in self.runners.copy().values():
            self.factory.delete_runner(runner)

