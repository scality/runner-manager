import json
import logging

from fastapi import FastAPI, Request, Form
from fastapi.responses import Response

from . import redis_database, runner_m, github_manager
from Webhook import Webhook

logger = logging.getLogger("runner_manager")
app = FastAPI()


@app.get("/")
async def root():
    keys = {}
    for elem in redis_database.keys():
        keys[elem] = redis_database.get(elem)

    return {"message": "Hello World", "redis_database": keys}


@app.post('/runners/refresh')
async def refresh_data(request: Request):
    try:
        runners = github_manager.get_runners()
        runner_m.update_all_runners(runners['runners'])
    except Exception as e:
        logger.info(e)
    return Response(status_code=200)


@app.post('/runners/reset')
async def reset_reset_runners(request: Request):
    runner_m.remove_all_runners()
    g_runners = github_manager.get_runners()
    runner_m.update_all_runners(g_runners['runners'])
    return Response(status_code=200)


@app.post('/webhook')
async def webhook_post(payload: str = Form(...), request: Request = None):
    Webhook(payload=json.loads(payload), event=request.headers['X-Github-Event'])()
    return Response(status_code=200)
