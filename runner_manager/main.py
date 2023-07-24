import logging
from functools import lru_cache
from typing import List

from fastapi import Depends, FastAPI
from redis_om import Migrator, get_redis_connection
from rq import Queue

from runner_manager.jobs.startup import startup
from runner_manager.dependencies import get_queue

log = logging.getLogger(__name__)

app = FastAPI()


@app.on_event("startup")
def startup_event():
    queue = get_queue()
    job = queue.enqueue(startup)
    status = job.get_status()
    log.info(f"Startup job is {status}")
