from pytest import fixture

from runner_manager.models.runner_group import RunnerGroup




@fixture()
def runner_group() -> RunnerGroup:
    runner_group = RunnerGroup(
        id=1,
        name="test",
        organization="test",
        backend="base",
        backend_config={},
        labels=[
            "label",
        ],
    )
    return runner_group
