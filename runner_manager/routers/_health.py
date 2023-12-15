import logging

from fastapi import APIRouter, Depends, Response
from redis import Redis

from runner_manager.dependencies import get_redis

router = APIRouter(prefix="/_health")

log = logging.getLogger(__name__)


@router.get("/", status_code=200)
def healthcheck(r: Redis = Depends(get_redis)):
    """Healthcheck endpoint that answers to GET requests on /_health"""

    try:
        r.ping()
    except Exception as exp:
        log.error("Redis healthcheck failed: %s", exp)
        return Response(status_code=500)

    return Response(status_code=200)
