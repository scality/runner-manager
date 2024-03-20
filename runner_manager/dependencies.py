from functools import lru_cache

import httpx
from githubkit.config import Config
from githubkit.retry import RetryRateLimit
from redis import Redis
from redis_om import get_redis_connection
from rq import Queue
from rq_scheduler import Scheduler

from runner_manager.clients.github import GitHub
from runner_manager.models.settings import Settings


@lru_cache()
def get_settings() -> Settings:
    return Settings()


@lru_cache()
def get_redis(decode=True) -> Redis:
    return get_redis_connection(
        url=get_settings().redis_om_url, decode_responses=decode
    )


@lru_cache
def get_queue() -> Queue:
    return Queue(connection=get_redis(decode=False))


@lru_cache()
def get_scheduler() -> Scheduler:
    queue: Queue = get_queue()
    return Scheduler(queue=queue, connection=queue.connection)


@lru_cache()
def get_github() -> GitHub:
    settings: Settings = get_settings()
    auto_retry = RetryRateLimit(max_retry=3) if settings.github_auto_retry else None
    config: Config = Config(
        base_url=httpx.URL(str(settings.github_base_url)),
        follow_redirects=True,
        accept="*/*",
        user_agent="runner-manager",
        timeout=httpx.Timeout(30.0),
        http_cache=True,
        auto_retry=auto_retry,
    )
    return GitHub(settings.github_auth_strategy(), config=config)
