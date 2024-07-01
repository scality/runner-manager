import logging

from fastapi import APIRouter, Response

router = APIRouter(prefix="/metrics")

log = logging.getLogger(__name__)


@router.get("/", status_code=200)
def metrics():
    """Metrics endpoint that answers to GET requests on /metrics"""

    return Response(status_code=200)
