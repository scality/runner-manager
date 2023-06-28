import json
import logging

import redis
from runners_manager.runner.Runner import Runner

logger = logging.getLogger("runner_manager")


class RedisManager(object):
    redis: redis.Redis

    def __init__(self, redis: redis.Redis):
        self.redis = redis
        if self.redis.get("settings:running") is None:
            self.redis.set("settings:running", str(True))

    def set_manager_running(self, status: bool):
        self.redis.set("settings:running", str(status))

    def get_manager_running(self):
        return b"True" == self.redis.get("settings:running")

    def get_all_runners_managers(self) -> list[str]:
        return [name.decode("ascii") for name in self.redis.keys("managers:*")]

    def get_all_runners(self) -> list[Runner]:
        return [self.get_runner(name) for name in self.redis.keys("runners:*")]

    def delete_runners_manager(self, runner_manager):
        self.redis.delete(runner_manager)

    def update_manager_runners(self, runner_manager: str, runners: list[Runner]):
        runners_name = [r.redis_key_name() for r in runners]
        self.redis.set(runner_manager, json.dumps(runners_name))

    def delete_runner(self, runner: Runner) -> None:
        self.redis.delete(runner.redis_key_name())

    def update_runner(self, runner: Runner) -> None:
        self.redis.set(runner.redis_key_name(), json.dumps(runner.toJson()))

    def get_runner(self, name: str) -> Runner:
        if not self.redis.get(name):
            return None
        data = json.loads(self.redis.get(name))
        return Runner.fromJson(data)

    def is_managed(self, name: str) -> bool:
        """
        For a given runner name, check if it is managed by the service.
        """
        runners: Runner = self.get_all_runners()
        for runner in runners:
            if name == runner.name:
                return True
        return False

    def get_runners(self, manager_name: str) -> dict[str, Runner]:
        """
        Get all runners name from the manager name and build each of them with there json
        """
        runner_names = self.redis.get(manager_name)
        if not runner_names:
            return {}

        runners_json = self.redis.mget(json.loads(runner_names))
        runners = {}
        for runner in runners_json:
            if runner:
                r = Runner.fromJson(json.loads(runner))
                runners[r.name] = r

        return runners

    def save_runners(self, runner_manager: str, runners: list[Runner]):
        """
        Save runners json data in redis, first we save the list of object for a manager
        Then we save each object with his name

        Set a dictionary with there name as keys and the json as value to save them all in one time
        """
        self.update_manager_runners(runner_manager, runners)

        d = {}
        for r in runners:
            d[r.redis_key_name()] = json.dumps(r.toJson())

        self.redis.mset(d)
