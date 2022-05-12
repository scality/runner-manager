import datetime
import logging
from collections.abc import Callable

from runners_manager.runner.RedisManager import RedisManager
from runners_manager.runner.Runner import Runner
from runners_manager.runner.RunnerFactory import RunnerFactory
from runners_manager.vm_creation.VmType import VmType

logger = logging.getLogger("runner_manager")


class RunnerManager(object):
    """
    This object creates, delete and update runners infos bout VM and github runner
    We save every info updated on the redis database
    This class is a tool and is here to join Github and local data
    """

    redis: RedisManager
    vm_type: VmType
    runners: dict[str, Runner]
    factory: RunnerFactory

    def __init__(self, vm_type: VmType, factory: RunnerFactory, redis: RedisManager):
        self.redis = redis
        self.vm_type = vm_type
        self.factory = factory
        self.runners = {}
        self.runners = self.redis.get_runners(self.redis_key_name())

    def get_runners(self) -> [Runner]:
        self.runners = self.redis.get_runners(self.redis_key_name())
        return self.runners

    def redis_key_name(self) -> str:
        """
        Define the redis key name for this instance
        :return:
        """
        return f'managers:{"-".join(self.vm_type.tags)}'

    def update_runner(self, github_runner: dict) -> None:
        self.runners = self.redis.get_runners(self.redis_key_name())
        if github_runner["name"] in self.runners:
            runner = self.runners[github_runner["name"]]
            runner.update_from_github(github_runner)
            self.redis.update_runner(runner)

    def update_runners(self, github_runners: list[dict]) -> None:
        """
        Update internal runners info from github.com
        :param github_runners:
        :return:
        """
        self.runners = self.redis.get_runners(self.redis_key_name())

        # Remove runners not listed on github
        github_r_names = [r["name"] for r in github_runners]
        runners_to_deletes = [
            name
            for name, r in self.get_runners().items()
            if name not in github_r_names and not r.is_creating
        ]
        for name in runners_to_deletes:
            self.delete_runner(self.runners[name])

        # Update status of each runner
        for elem in github_runners:
            self.update_runner(elem)

    def create_runner(self) -> None:
        self.runners = self.redis.get_runners(self.redis_key_name())
        runner = self.factory.create_runner(self.vm_type)
        runner.update_status("creating")
        self.runners[runner.name] = runner

        self.redis.update_runner(runner)
        self.redis.update_manager_runners(
            self.redis_key_name(), list(self.runners.values())
        )

    def delete_runner(self, runner: Runner) -> None:
        self.runners = self.redis.get_runners(self.redis_key_name())
        runner.update_status("deleting")
        self.factory.delete_runner(runner)
        del self.runners[runner.name]

        self.redis.delete_runner(runner)
        self.redis.update_manager_runners(
            self.redis_key_name(), list(self.runners.values())
        )

        del runner

    def respawn_runner(self, runner: Runner) -> None:
        self.runners = self.redis.get_runners(self.redis_key_name())
        runner.update_status("respawning")
        self.runners[runner.name] = runner
        self.factory.respawn_replace(runner)
        self.redis.update_runner(runner)

    def runners_not_used_for(self, duration: datetime.timedelta) -> [Runner]:
        self.runners = self.redis.get_runners(self.redis_key_name())
        return self.filter_runners(
            lambda runner: runner.status == "online"
            and not runner.has_run
            and runner.time_online > duration
        )

    def filter_runners(self, cond: Callable[[Runner], bool]) -> [Runner]:
        """
        Return a list of runner matching the condition function
        :param cond:
        :return:
        """
        self.runners = self.redis.get_runners(self.redis_key_name())
        return list(
            filter(
                lambda e: (
                    e.name.startswith(self.factory.runner_prefix)
                    and e.vm_type.tags == self.vm_type.tags
                    and cond(e)
                ),
                self.runners.values(),
            )
        )

    def min_runner_number(self) -> int:
        return self.vm_type.quantity["min"]

    def max_runner_number(self) -> int:
        return self.vm_type.quantity["max"]
