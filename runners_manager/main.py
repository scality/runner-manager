import time
import logging

from vm_creation.github_actions_api import get_runners
from runner.RunnerManager import RunnerManager

logger = logging.getLogger("runner_manager")


def maintain_number_of_runner(runner_m: RunnerManager):
    while True:
        runners = get_runners(runner_m.github_organization)
        logger.info(f"nb runners: {len(runners['runners'])}")
        logger.info(
            f"offline: {len([e for e in runners['runners'] if e['status'] == 'offline'])}"
        )

        logger.debug(runners)
        runner_m.update(runners['runners'])

        time.sleep(5)


def main(org):
    config = [{
        'tags': ['centos7', 'small'],
        'flavor': 'm1.small',
        'image': 'CentOS 7 (PVHVM)',
        'quantity': {
            'min': 2,
            'max': 4,
        },
    }]
    runner_m = RunnerManager(org, config)
    maintain_number_of_runner(runner_m)
