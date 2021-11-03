from runners_manager.settings.yaml_config import setup_settings, EnvSettings
from runners_manager.main import main


def start():
    args = EnvSettings()
    if not(args.cloud_nine_user and args.cloud_nine_password) and not args.cloud_nine_token:
        raise Exception('You should have infos for openstack / cloud nine connection')

    settings = setup_settings(args.setting_file)
    main(settings, args)


if __name__ == "__main__":
    start()
