import os

import runners_manager.settings.settings_local # noqa
from runners_manager.main import main


organization = os.getenv('GITHUB_ORGANIZATION')


def start():
    main(organization)


if __name__ == "__main__":
    start()
