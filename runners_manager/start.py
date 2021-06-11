import os

import settings.settings_local
from main import main


organization = os.getenv('GITHUB_ORGANIZATION')


def start():
    main(organization)


if __name__ == "__main__":
    start()
