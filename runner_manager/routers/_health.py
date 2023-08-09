
from fastapi import APIRouter, Response

router = APIRouter(prefix="/_health")


@router.get("/", status_code=200)
def healthcheck():
    """Healthcheck endpoint that answers to GET requests on /_healthz"""
    return Response(status_code=200)
