from runner_manager.dependencies import get_settings
from runner_manager.models.runner_group import RunnerGroup
from runner_manager.models.settings import Settings


def create_runner_group(settings: Settings = get_settings()):
    runner_groups_configs = settings.runner_groups
    existing_groups = RunnerGroup.find().all()
    for runner_group_config in runner_groups_configs:
        if runner_group_config.name not in [group.name for group in existing_groups]:
            runner_group = runner_group_config.save()
        else:
            runner_group = RunnerGroup.find(RunnerGroup.name == runner_group_config.name).first()
            runner_group.update(runner_group_config)
            existing_groups.remove(runner_group)
    for runner_group in existing_groups:
        runner_group.delete()
