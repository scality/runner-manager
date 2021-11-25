import datetime
import logging

from runners_manager.runner.Runner import Runner
from runners_manager.vm_creation.github_actions_api import GithubManager
from runners_manager.vm_creation.openstack import OpenstackManager
from runners_manager.runner.RunnerFactory import RunnerFactory
from runners_manager.runner.RunnerManager import RunnerManager
from runners_manager.runner.VmType import VmType
from runners_manager.runner.RedisManager import RedisManager

logger = logging.getLogger("runner_manager")


class Manager(object):
    """
    This object contain the main logic to maintain the number of needed runners
    It manage all runners for one repository
    """
    factory: RunnerFactory
    runner_managers: list[RunnerManager]
    extra_runner_online_timer: datetime.timedelta
    timeout_runner_timer: datetime.timedelta

    def __init__(self, settings: dict,
                 openstack_manager: OpenstackManager,
                 github_manager: GithubManager,
                 r: RedisManager):
        self.factory = RunnerFactory(openstack_manager,
                                     github_manager,
                                     settings['github_organization'],
                                     r)
        self.runner_managers = []
        for v_type in settings['runner_pool']:
            self.runner_managers.append(RunnerManager(VmType(v_type), self.factory, r))

        self.extra_runner_online_timer = datetime.timedelta(**settings['extra_runner_timer'])
        self.timeout_runner_timer = datetime.timedelta(**settings['timeout_runner_timer'])
        self.redis = r
        self.synchronize_managed_runner_with_local_settings()

    def remove_all_runners(self):
        for manager in self.runner_managers:
            for runner in manager.get_runners().values():
                if not runner.is_running:
                    manager.delete_runner(runner)

        # Remove orphan runners
        for runner in self.redis.get_all_runners():
            if runner:
                self.factory.delete_runner(runner)
                self.redis.delete_runner(runner)

    def synchronize_managed_runner_with_local_settings(self):
        for key_runners_manager in self.redis.get_all_runners_managers():
            logger.info(key_runners_manager)
            # If the runner manager is not in the local manager runner delete it
            if key_runners_manager not in [rm.redis_key_name() for rm in self.runner_managers]:
                for name, runner in self.redis.get_runners(key_runners_manager).items():
                    self.factory.delete_runner(runner)
                    self.redis.delete_runner(runner)
                self.redis.delete_runners_manager(key_runners_manager)

    def update_all_runners(self, github_runners: list[dict]):
        """
        Here we update runners states with github api data
        And recalculate the need to spawn or delete runners
        :param github_runners:  Github api infos about self-hosted runners
        """
        for runner_manager in self.runner_managers:
            runner_manager.update_runners(github_runners)

        self.log_runners_infos()
        self.manage_runners()

    def update_runner_status(self, runner: dict):
        logger.info(runner)
        manager = next(
            manager for manager in self.runner_managers if runner["name"] in manager.runners.keys()
        )

        logger.info(manager)
        manager.update_runner(runner)
        self.log_runners_infos()
        self.manage_runners()

    def manage_runners(self):
        # runner logic For each type of VM
        for manager in self.runner_managers:
            # Always Respawn Vm
            offline_runners = manager.filter_runners(lambda r: r.has_run)
            for r in offline_runners:
                manager.respawn_runner(r)

            # Create if it's still not enough
            while self.need_new_runner(manager):
                manager.create_runner()

            # Respawn runner if they are offline for more then 10min after spawn
            for elem in manager.filter_runners(self.runner_should_never_spawn):
                manager.respawn_runner(elem)

            # Delete last runners if you have too many and they are not used for the last x minutes
            runners_to_delete = manager.filter_runners(
                self.too_much_runner_online
            )[manager.min_runner_number():]
            for runner in runners_to_delete:
                manager.delete_runner(runner)

    @staticmethod
    def need_new_runner(manager: RunnerManager) -> bool:
        """
        This function define if we need new runners or not.
        This logic is based on the statement: They should be always x runner waiting,
            when x is the `min` variable set in the config file
        :param manager: RunnerManager
        :return: True if can and need a new runner
        """

        current_online_or_creating = len(
            manager.filter_runners(lambda r: r.is_online or r.is_creating)
        )
        current_running = len(manager.filter_runners(lambda r: r.is_running))

        return current_online_or_creating < manager.min_runner_number() and \
            current_running + current_online_or_creating < manager.max_runner_number()

    def too_much_runner_online(self, runner: Runner) -> bool:
        return runner.is_online and not runner.has_run \
            and runner.time_online > self.extra_runner_online_timer

    def runner_should_never_spawn(self, runner: Runner) -> bool:
        return runner.is_creating \
            and runner.time_since_created > self.timeout_runner_timer

    def log_runners_infos(self):
        for manager in self.runner_managers:
            offline_runners = manager.filter_runners(lambda r: r.has_run)
            creating_runners = manager.filter_runners(lambda r: r.is_creating)
            online_runners = manager.filter_runners(lambda r: r.is_online)

            logger.info("type" + str(manager.vm_type))
            logger.debug('Online runners')
            logger.debug(','.join([f"{elem.name} {elem.status}" for elem in online_runners]))
            logger.debug('Creating runners')
            logger.debug(','.join([f"{elem.name} {elem.status}" for elem in creating_runners]))
            logger.debug('Offline runners')
            logger.debug(','.join([f"{elem.name} {elem.status}" for elem in offline_runners]))
