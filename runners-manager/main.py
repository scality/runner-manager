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

        for elem in runners['runners']:
            runner_m.update_runner(elem)

        time.sleep(5)


def main():
    org = 'scalanga-devl'
    config = [{
        'tags': ['centos7', 'small'],
        'flavor': 'm1.small',
        'image': 'CentOS 7 (PVHVM)',
        'quantity': 2,
    }, {
        'tags': ['ubuntu', '16.04', 'small'],
        'flavor': 'm1.small',
        'image': 'Ubuntu 16.04 LTS (Xenial Xerus) (PVHVM)',
        'quantity': 2,
    }]
    runner_m = RunnerManager(org, config)
    maintain_number_of_runner(runner_m)


if __name__ == "__main__":
    runners = get_runners('scalanga-devl')
    pprint.pprint(runners)
    for elem in runners['runners']:
        force_delete_runner('scalanga-devl', elem['id'])
    # s.enter(60, 1, main, (s,))
    # s.run()
    main()
