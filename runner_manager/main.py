import logging
from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import FastAPI
from redis import Redis
from rq.job import Job
from rq_scheduler import Scheduler

from runner_manager.auth import TrustedHostHealthRoutes
from runner_manager.dependencies import (
    get_queue,
    get_redis,
    get_scheduler,
    get_settings,
)
from runner_manager.jobs.startup import startup
from runner_manager.models.runner import Runner
from runner_manager.models.runner_group import RunnerGroup
from runner_manager.models.settings import Settings
from runner_manager.routers import _health, private, public, runner_groups, webhook

log = logging.getLogger(__name__)
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Context manager to run startup and shutdown events."""
    scheduler: Scheduler = get_scheduler()
    redis: Redis = get_redis()
    get_queue()
    settings: Settings = get_settings()
    log.info(f"Starting up {settings.name}")
    log.info("Configuring redis models")
    Runner.Meta.database = redis
    RunnerGroup.Meta.database = redis
    log.info("Configuring scheduler")
    job: Job = scheduler.schedule(
        scheduled_time=datetime.utcnow(),
        func=startup,
        args=[settings],
        interval=settings.healthcheck_interval,
        repeat=None,
    )
    yield
    log.info(f"Shutting down {settings.name}")
    scheduler.cancel(job)


app = FastAPI(
    lifespan=lifespan,
)


app.include_router(webhook.router)
app.include_router(_health.router)
app.include_router(private.router)
app.include_router(public.router)
app.include_router(runner_groups.router)
app.add_middleware(TrustedHostHealthRoutes, allowed_hosts=settings.allowed_hosts)
