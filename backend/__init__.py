import logging

from settings.yaml_config import setup_settings, EnvSettings
from runners_manager.main import init


logger = logging.getLogger("runner_manager")
args = EnvSettings()

if not (args.cloud_nine_user and args.cloud_nine_password) and not args.cloud_nine_token:
    raise Exception('You should have infos for openstack / cloud nine connection')

settings = setup_settings(args.setting_file)
runner_m, redis_database, github_manager, openstack_manager = init(settings, args)
r = github_manager.get_runners()
logger.info(r)
runner_m.update_all_runners(r['runners'])
