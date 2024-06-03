import logging

from fastapi import APIRouter, Depends, Response
from redis import Redis
from rq import Queue, Retry

from runner_manager.dependencies import get_queue, get_redis
from runner_manager.jobs.startup import indexing

router = APIRouter(prefix="/_health")

log = logging.getLogger(__name__)


@router.get("/", status_code=200)
def healthcheck(r: Redis = Depends(get_redis), queue: Queue = Depends(get_queue)):
    """Healthcheck endpoint that answers to GET requests on /_health"""

    try:
        r.ping()
    except Exception as exp:
        log.error("Redis healthcheck failed: %s", exp)
        # In the case where redis is rebooting
        # when the service will be back up,
        # it will need to create indexes for search to work
        queue.enqueue(indexing, retry=Retry(max=3, interval=[30, 60, 120]))
        return Response(status_code=500)

    return Response(status_code=200)
