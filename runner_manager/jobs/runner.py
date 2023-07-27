from runner_manager.models.runner import Runner


def create_runner(runner: Runner) -> Runner:
    return runner.save()
