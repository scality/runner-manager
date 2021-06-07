import os
import sched
import time
import pprint
from vm_creation.github_actions_api import get_runners, force_delete_runner
from runner.RunnerManager import RunnerManager

s = sched.scheduler(time.time, time.sleep)

pprint = pprint.PrettyPrinter()


def maintain_number_of_runner(runner_m: RunnerManager):
    while True:
        runners = get_runners(runner_m.github_organization)
        print(f"nb runners: {len(runners['runners'])}")
        print(
            f"offline: {len([e for e in runners['runners'] if e['status'] == 'offline'])}"
        )

        print(runners)
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


if __name__ == "__main__":
    organization = os.getenv('GITHUB_ORGANIZATION')
    runners = get_runners(organization)
    pprint.pprint(runners)
    for elem in runners['runners']:
        force_delete_runner(organization, elem['id'])
    # s.enter(60, 1, main, (s,))
    # s.run()
    main(organization)
