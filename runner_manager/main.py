from contextlib import asynccontextmanager

from fastapi import FastAPI
from redis import Redis
from rq import Queue
from rq.job import Job

from runner_manager import Runner, RunnerGroup, Settings, log
from runner_manager.dependencies import get_queue, get_redis, get_settings
from runner_manager.jobs.startup import startup
from runner_manager.routers import _health, private, public, runner_groups, webhook

settings = get_settings()
log.setLevel(settings.log_level)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Context manager to run startup and shutdown events."""
    redis: Redis = get_redis()
    queue: Queue = get_queue()
    settings: Settings = get_settings()
    log.info(f"Starting up {settings.name}")
    log.info("Configuring redis models")
    Runner.Meta.database = redis
    RunnerGroup.Meta.database = redis
    job: Job = queue.enqueue(startup, settings=settings)
    log.info(f"Startup job {job.id} is {job.get_status()}")
    yield
    log.info(f"Shutting down {settings.name}")


app = FastAPI(
    lifespan=lifespan,
)

app.include_router(webhook.router)
app.include_router(_health.router)
app.include_router(private.router)
app.include_router(public.router)
app.include_router(runner_groups.router)


@app.get("/")
def homepage():
    """
    Homepage
    """
    return {"message": "Hello World"}
