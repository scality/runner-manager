
"""Jobs to run on startup."""

from redis_om import Migrator


def startup():
    return Migrator().run()
