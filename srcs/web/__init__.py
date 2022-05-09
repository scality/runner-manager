from runners_manager.main import init
from settings.yaml_config import EnvSettings, setup_settings

args = EnvSettings()
settings = setup_settings(args.setting_file)
runner_m, redis_database, github_manager, openstack_manager = init(settings, args)
