from runners_manager.main import main
from settings.yaml_config import setup_settings, EnvSettings


def start():
    args = EnvSettings()
    settings = setup_settings(args.setting_file)
    main(settings, args)


if __name__ == "__main__":
    start()
