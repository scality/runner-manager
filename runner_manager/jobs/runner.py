from runner_manager import RunnerGroup
from runner_manager.clients.github import GitHub
from runner_manager.dependencies import get_github


def create_runner(group: RunnerGroup) -> str | None:
    github: GitHub = get_github()
    runner = group.create_runner(github)
    if runner is not None:
        return runner.pk
