import sched, time, pprint
from vm_creation.github_actions_api import infos_runners, create_runner_token, force_delete_runner
from vm_creation.openstack import create_vm, delete_vm

s = sched.scheduler(time.time, time.sleep)

pprint = pprint.PrettyPrinter()
WHANTED_MACHINES = {
    'centos-8': 2,
}


def remove_runner(org, runner_id, vm_id):
    force_delete_runner(org, runner_id)
    delete_vm(vm_id)


def create_runner(org, runner_counter):
    print(f'create runner: {runner_counter}')
    token = create_runner_token(org)
    return create_vm(name=runner_counter, runner_token=token)


def replace_finish_runner(org, runner_counter, to_replace):
    vm_id = create_runner(org, str(runner_counter))
    new_runner = {
        'name': str(runner_counter),
        'action_id': None,
        'vm_id': vm_id,
        'has_run': False,
        'parent_name': to_replace['name']
    }
    runner_counter += 1
    return new_runner, runner_counter

# runner_infos[str(runner_counter)] =

def maintain_number_of_runner(org, runner_counter, runner_infos):
    """
    check this file if there is an error: sudo cat /var/log/messages
    :param org: 
    :param runner_counter: 
    :param runner_infos: 
    :return: 
    """
    runners = infos_runners(org)
    pprint.pprint(runners)
    while True:
        runners = infos_runners(org)
        print(f"nb runners: {len(runners['runners'])}")
        print(f"offline: {len([elem for elem in runners['runners'] if elem['status'] == 'offline'])}")

        for elem in runners['runners']:
            if runner_infos[elem['name']]['action_id'] is None:
                pprint.pprint(runner_infos)
                runner_infos[elem['name']]['action_id'] = elem['id']

            if elem['status'] == 'offline' and runner_infos[elem['name']]['has_run'] and not any(key for (key, value) in runner_infos.items() if value['parent_name'] == elem['name']):
                new_runner, runner_counter = replace_finish_runner(org, runner_counter, elem)
                runner_infos[new_runner['name']] = new_runner

            if not runner_infos[elem['name']]['has_run'] and elem['status'] != 'offline':
                print(f'runner {elem["name"]} started !')
                r = runner_infos[elem['name']]
                r['has_run'] = True
                runner_infos[elem['name']] = r

                parent_name = runner_infos[elem['name']]['parent_name']
                if parent_name:
                    print(f"deleting {parent_name}")
                    remove_runner(org, runner_infos[parent_name]['action_id'], runner_infos[parent_name]['vm_id'])

        time.sleep(5)


def init_runners(org, runner_counter, runner_infos):
    runners = infos_runners(org)
    pprint.pprint(runners)
    for index in range(0, WHANTED_MACHINES['centos-8'] - runners['total_count']):
        vm_id = create_runner(org, str(runner_counter))
        runner_infos[str(runner_counter)] = {
            'name': str(runner_counter),
            'action_id': None,
            'vm_id': vm_id,
            'has_run': False,
            'parent_name': None
        }

        runner_counter += 1

    return runner_counter, runner_infos


def main():
    org = 'scalanga-devl'
    runner_counter = 0
    runner_infos = {}
    runner_counter, runner_infos = init_runners(org, runner_counter, runner_infos)
    maintain_number_of_runner(org, runner_counter, runner_infos)


if __name__ == "__main__":
    runners = infos_runners('scalanga-devl')
    pprint.pprint(runners)
    for elem in runners['runners']:
        force_delete_runner('scalanga-devl', elem['id'])
    # s.enter(60, 1, main, (s,))
    # s.run()
    main()
