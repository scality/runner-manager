import logging

from fastapi import Depends, FastAPI
from rq import Queue
from redis import Redis

from runner_manager.dependencies import get_queue, get_settings, get_redis
from runner_manager.jobs.startup import startup
from runner_manager.routers import _health, private, public, webhook
from runner_manager.auth import TrustedHostHealthRoutes
from runner_manager import Settings
from runner_manager import Runner, RunnerGroup

log = logging.getLogger(__name__)
app = FastAPI()
settings = get_settings()


app.include_router(webhook.router)
app.include_router(_health.router)
app.include_router(private.router)
app.include_router(public.router)
app.add_middleware(TrustedHostHealthRoutes, allowed_hosts=settings.allowed_hosts)


@app.on_event("startup")
def startup_event(
    redis: Redis = Depends(get_redis),
    queue: Queue = Depends(get_queue),
    settings: Settings = Depends(get_settings)
):
    job = queue.enqueue(startup)
    status = job.get_status()
    Runner.Meta.global_key_prefix = settings.name
    Runner.Meta.database = redis
    RunnerGroup.Meta.global_key_prefix = settings.name
    RunnerGroup.Meta.database = redis
    log.info(f"Startup job is {status}")
