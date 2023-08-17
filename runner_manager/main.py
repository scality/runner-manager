import logging

from fastapi import FastAPI
from redis import Redis
from rq import Queue

from runner_manager import Runner, RunnerGroup, Settings
from runner_manager.dependencies import get_queue, get_redis, get_settings
from runner_manager.jobs.startup import startup
from runner_manager.routers import _health, private, public, webhook

log = logging.getLogger(__name__)
settings: Settings = get_settings()
queue: Queue = get_queue()
redis: Redis = get_redis()
app = FastAPI()


app.include_router(webhook.router)
app.include_router(_health.router)
app.include_router(private.router)
app.include_router(public.router)


@app.on_event("startup")
def startup_event():
    job = queue.enqueue(startup)
    status = job.get_status()
    Runner.Meta.database = redis
    RunnerGroup.Meta.database = redis
    log.info(f"Startup job is {status}")
