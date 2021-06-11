import time
import logging

from vm_creation.github_actions_api import get_runners, force_delete_runner
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
    runners = get_runners(org)
    logger.debug("Delete all runners")
    logger.debug(runners)
    for elem in runners['runners']:
        force_delete_runner(org, elem['id'])

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
