import datetime
import logging
import redis

from runners_manager.runner.Runner import Runner
from runners_manager.vm_creation.github_actions_api import GithubManager
from runners_manager.vm_creation.openstack import OpenstackManager
from runners_manager.runner.RunnerFactory import RunnerFactory
from runners_manager.runner.RunnerManager import RunnerManager
from runners_manager.runner.VmType import VmType

logger = logging.getLogger("runner_manager")


class Manager(object):
    """
    This object contain the main logic to maintain the number of needed runners
    """
    factory: RunnerFactory
    redis: redis.Redis
    runner_managers: list[RunnerManager]
    extra_runner_online_timer: dict

    def __init__(self, settings: dict,
                 openstack_manager: OpenstackManager,
                 github_manager: GithubManager,
                 r: redis.Redis):
        self.factory = RunnerFactory(openstack_manager,
                                     github_manager,
                                     settings['github_organization'])
        self.redis = r
        self.runner_managers = []
        for v_type in settings['runner_pool']:
            self.runner_managers.append(RunnerManager(VmType(v_type), self.factory, self.redis))

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
                manager.respawn_runner(r)

            # Create if it's still not enough
            while manager.need_new_runner():
                manager.create_runner()

            # Respawn runner if they are offline for more then 10min after spawn
            for elem in manager.filter_runners(self.runner_should_never_spawn):
                manager.respawn_runner(elem)

            # Delete if you have too many and they are not used for the last x hours / minutes
            for runner in manager.filter_runners(self.need_less_runner):
                if manager.too_much_runner():
                    manager.delete_runner(runner)

    def need_less_runner(self, runner: Runner) -> bool:
        return runner.status == 'online' and not runner.has_run \
            and runner.time_online > datetime.timedelta(**self.extra_runner_online_timer)

    @staticmethod
    def runner_should_never_spawn(runner: Runner) -> bool:
        # TODO add this 15 min timer in the config file
        return runner.status == 'offline' and not runner.has_run \
            and runner.time_since_created > datetime.timedelta(minutes=15)

    def log_runners_infos(self):
        for manager in self.runner_managers:
            offline_runners = manager.filter_runners(lambda r: r.has_run)
            online_runners = manager.filter_runners(lambda r: r.status == 'online')

            logger.info("type" + str(manager.vm_type))
            logger.debug('Online runners')
            logger.debug(','.join([f"{elem.name} {elem.status}" for elem in online_runners]))
            logger.debug('Offline runners')
            logger.debug(','.join([f"{elem.name} {elem.status}" for elem in offline_runners]))
