from fastapi import APIRouter, Response, Request
from githubkit.webhooks import parse
from githubkit.webhooks.types import WebhookEvent

router = APIRouter(prefix="/webhook")


@router.get("/")
def get():
    return Response(content="Success", status_code=200)

@router.post("/")
def webhook(request: Request):
    #event: WebhookEvent = parse(request.headers["X-GitHub-Event"], request.body())
    return Response(content="Success", status_code=200)
