#!/usr/bin/env python

from redis import Redis
from rq_scheduler import Scheduler
from rq_scheduler.utils import setup_loghandlers

from runner_manager.dependencies import get_redis


def run():
    redis: Redis = get_redis(decode=False)
    level: str = "INFO"
    setup_loghandlers(level)
    scheduler = Scheduler(connection=redis, interval=30)
    scheduler.run(burst=False)


if __name__ == "__main__":
    run()
