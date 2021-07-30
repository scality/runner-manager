import datetime
import logging
from collections.abc import Callable


from runners_manager.runner.Runner import Runner
from runners_manager.vm_creation.github_actions_api import GithubManager
from runners_manager.vm_creation.openstack import OpenstackManager
from runners_manager.runner.RunnerFactory import RunnerFactory
from runners_manager.runner.RunnerManager import RunnerManager
from runners_manager.runner.VmType import VmType

logger = logging.getLogger("runner_manager")


class Manager(object):
    factories: RunnerFactory
    runner_managers: list[RunnerManager]
    extra_runner_online_timer: dict

    def __init__(self, settings: dict,
                 openstack_manager: OpenstackManager,
                 github_manager: GithubManager):
        self.factory = RunnerFactory(openstack_manager, github_manager, settings['github_organization'])
        self.runner_managers = [RunnerManager(VmType(elem), self.factory) for elem in settings['runner_pool']]
        self.extra_runner_online_timer = settings['extra_runner_timer']

    def update(self, github_runners: list[dict]):
        for runner_manager in self.runner_managers:
            runner_manager.update(github_runners)

        self.log_runners_infos()

        # runner logic For each type of VM
        for manager in self.runner_managers:
            # Always Respawn Vm
            offline_runners = manager.filter_runners(lambda r: r.has_run)
            for r in offline_runners:
                self.factory.respawn_replace(r)

            # Create if it's still not enough
            while manager.need_new_runner():
                manager.create_runner()

            # Respawn runner if they are offline for more then 10min after spawn
            # TODO add this timer in the config file
            for elem in manager.filter_runners(self.runner_should_never_spawn):
                self.factory.respawn_replace(elem)

            # Delete if you have too many and they are not used for the last x hours / minutes
            for runner in manager.filter_runners(self.need_less_runner(manager)):
                if runner.time_online > datetime.timedelta(**self.extra_runner_online_timer) \
                        and manager.too_much_runner():
                    manager.delete_runner(runner)

    def need_less_runner(self, manager: RunnerManager) -> Callable[Runner, bool]:
        return lambda runner: runner.status == 'offline' and not runner.has_run \
                and runner.time_online > datetime.timedelta(**self.extra_runner_online_timer) \
                and manager.too_much_runner()

    @staticmethod
    def runner_should_never_spawn(runner: Runner) -> bool:
        time_since_spawn = datetime.datetime.now() - runner.created_at
        return runner.status == 'offline' and not runner.has_run \
               and time_since_spawn > datetime.timedelta(minutes=15)

    def log_runners_infos(self):
        for manager in self.runner_managers:
            offline_runners = manager.filter_runners(lambda r: r.has_run)
            online_runners = manager.filter_runners(lambda r: r.status == 'online')

            logger.info("type" + str(manager.vm_type))
            logger.debug('Online runners')
            logger.debug(','.join([f"{elem.name} {elem.status}" for elem in online_runners]))
            logger.debug('Offline runners')
            logger.debug(','.join([f"{elem.name} {elem.status}" for elem in offline_runners]))
