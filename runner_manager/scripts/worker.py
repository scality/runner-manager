#!/usr/bin/env python

from redis import Redis
from rq import Queue, Worker

from runner_manager.dependencies import get_queue, get_redis


def run():

    redis: Redis = get_redis()
    queue: Queue = get_queue()
    worker = Worker(
        queues=[queue],
        connection=redis,
    )
    worker.work(with_scheduler=True)


if __name__ == "__main__":
    run()
