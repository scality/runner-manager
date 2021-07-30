import datetime
import logging
from collections.abc import Callable


from runners_manager.runner.Runner import Runner
from runners_manager.vm_creation.github_actions_api import GithubManager
from runners_manager.vm_creation.openstack import OpenstackManager
from runners_manager.runner.RunnerFactory import RunnerFactory
from runners_manager.runner.VmType import VmType

logger = logging.getLogger("runner_manager")


class RunnerManager(object):
    runner_counter: int
    github_organization: str

    factories: RunnerFactory
    runners: dict[str, Runner]
    runner_management: list[VmType]
    extra_runner_online_timer: dict

    def __init__(self, settings: dict,
                 openstack_manager: OpenstackManager,
                 github_manager: GithubManager):
        self.runner_counter = 0

        self.github_organization = settings['github_organization']
        self.runner_management = [VmType(elem) for elem in settings['runner_pool']]
        self.extra_runner_online_timer = settings['extra_runner_timer']

        self.runners = {}
        self.factory = RunnerFactory(openstack_manager, github_manager, settings['github_organization'])

    def update(self, github_runners: list[dict]):
        # Update status of each runner
        for elem in github_runners:
            runner = self.runners[elem['name']]
            runner.update_status(elem)

            if runner.action_id is None:
                runner.action_id = elem['id']

        self.log_runners_infos()

        # runner logic For each type of VM
        for vm_type in self.runner_management:
            # Always Respawn Vm
            offline_runners = self.filter_runners(vm_type, lambda r: r.has_run)
            for r in offline_runners:
                self.factory.respawn_replace(r)

            # Create if it's still not enough
            while self.need_new_runner(vm_type):
                r = self.factory.create_runner(vm_type)
                self.runners[r.name] = r

            # Respawn runner if they are offline for more then 10min after spawn
            for elem in self.filter_runners(vm_type, lambda r: r.status == 'offline'):
                time_since_spawn = datetime.datetime.now() - elem.created_at
                if elem.has_run is False \
                        and time_since_spawn > datetime.timedelta(minutes=15):
                    self.factory.respawn_replace(elem)

            # Delete if you have too many and they are not used for the last x hours / minutes
            for elem in self.filter_runners(vm_type, lambda r: r.status == 'online'):
                if elem.time_online > datetime.timedelta(**self.extra_runner_online_timer) \
                        and self.too_much_runner(vm_type):
                    self.factory.delete_runner(elem)
                    del self.runners[elem.name]

    def too_much_runner(self, vm_type: VmType):
        current_online = len(
            self.filter_runners(vm_type, lambda r: r.action_id and r.status == 'online')
        )
        return current_online > vm_type.quantity['min']

    def need_new_runner(self, vm_type: VmType):
        """
        This function define if we need new runners or not.
        This logic is based on the statement: They should be always x runner waiting,
            when x is the `min` variable set in the config file
        :param vm_type: Type of runner
        :return: True if can and need a new runner
        """
        current_online_or_creating = len(
            self.filter_runners(vm_type, lambda r: not r.has_run and not r.status == 'running')
        )
        current_running = len(self.filter_runners(vm_type, lambda r: r.status == 'running'))

        return current_online_or_creating < vm_type.quantity['min'] and \
            current_running + current_online_or_creating < vm_type.quantity['max']

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

    def log_runners_infos(self):
        for vm_type in self.runner_management:
            offline_runners = self.filter_runners(vm_type, lambda r: r.has_run)
            online_runners = self.filter_runners(vm_type, lambda r: r.status == 'online')

            logger.info("type" + str(vm_type))
            logger.debug('Online runners')
            logger.debug(','.join([f"{elem.name} {elem.status}" for elem in online_runners]))
            logger.debug('Offline runners')
            logger.debug(','.join([f"{elem.name} {elem.status}" for elem in offline_runners]))

    def __del__(self):
        """
        Here we delete the runners currently in the manager
        TODO Remove this function when we have a persistent database
        :return:
        """
        for runner in self.runners.copy().values():
            self.factory.delete_runner(runner)
