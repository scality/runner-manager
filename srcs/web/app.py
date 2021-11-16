import logging

from fastapi import FastAPI, Request
from fastapi.responses import Response

from web import redis_database, runner_m, github_manager
from web.Webhook import Webhook
from runners_manager.monitoring.prometheus import prometheus_metrics

logger = logging.getLogger("runner_manager")
app = FastAPI()


app.add_route('/metrics', prometheus_metrics)


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
    logger.info(g_runners)
    logger.info(g_runners)
    logger.info(g_runners)
    runner_m.update_all_runners(g_runners['runners'])
    return Response(status_code=200)


@app.post('/webhook')
async def webhook_post(request: Request = None):
    data = await request.json()
    Webhook(payload=data, event=request.headers['X-Github-Event'])()
    return Response(status_code=200)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("web.app:app", host="0.0.0.0", port=8080, debug=True, reload='/app/srcs')
