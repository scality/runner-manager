#!/usr/bin/env python

import argparse

from rq import Queue
from rq_scheduler.scheduler import Scheduler

from runner_manager import Settings
from runner_manager.dependencies import get_queue, get_settings
from runner_manager.logging import log


def main():
    parser = argparse.ArgumentParser(description="Scheduler for the runner-manager")
    parser.add_argument(
        "-b",
        "--burst",
        action="store_true",
        default=False,
        help="Run in burst mode (quit after all work is done)",
    )
    args = parser.parse_args()

    queue: Queue = get_queue()
    settings: Settings = get_settings()
    log.setLevel(settings.log_level)

    log.info("Booting up scheduler")

    scheduler = Scheduler(
        queue=queue,
        connection=queue.connection,
    )
    scheduler.run(burst=args.burst)


if __name__ == "__main__":
    main()
