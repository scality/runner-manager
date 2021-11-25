import logging

from fastapi import FastAPI, Request
from fastapi.responses import Response
from fastapi_utils.tasks import repeat_every

from web import redis_database, runner_m, github_manager
from web.WebhookManager import WebHookManager
from web.models import WebHook
from runners_manager.monitoring.prometheus import prometheus_metrics

logger = logging.getLogger("runner_manager")
app = FastAPI()


app.add_route('/metrics', prometheus_metrics)


# TODO if we have multiple instances it might bug ?
@app.on_event("startup")
@repeat_every(seconds=60 * 2)
def refresh():
    logger.info("Refresh runners")
    try:
        runners = github_manager.get_runners()
        runner_m.update_all_runners(runners['runners'])
    except Exception as e:
        logger.info(e)


@app.get("/")
async def root():
    keys = {}
    for elem in redis_database.redis.keys():
        keys[elem] = redis_database.redis.get(elem)

    return {"message": "Hello World", "redis_database": keys}


@app.post('/runners/refresh')
async def refresh_data():
    await refresh()
    return Response(status_code=200)


@app.post('/runners/reset')
async def reset_reset_runners(request: Request):
    g_runners = github_manager.get_runners()
    runner_m.update_all_runners(g_runners['runners'])
    runner_m.remove_all_runners()
    g_runners = github_manager.get_runners()
    runner_m.update_all_runners(g_runners['runners'])
    return Response(status_code=200)


@app.post('/webhook')
async def webhook_post(data: WebHook, request: Request):
    WebHookManager(payload=data, event=request.headers['X-Github-Event'])()
    return Response(status_code=200)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("web.app:app", host="0.0.0.0", port=8080, debug=True, reload='/app/srcs')
