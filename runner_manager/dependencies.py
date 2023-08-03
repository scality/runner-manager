from functools import lru_cache

from redis import Redis
from redis_om import get_redis_connection
from rq import Queue

from runner_manager.models.settings import Settings


@lru_cache()
def get_settings() -> Settings:
    return Settings()


def get_redis() -> Redis:
    return get_redis_connection(url=get_settings().redis_om_url, decode_responses=True)


def get_queue() -> Queue:
    return Queue(connection=get_redis())
