import logging
from redis import Redis

from fastapi import Depends, FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.responses import Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi_utils.tasks import repeat_every
from functools import lru_cache
from runners_manager.monitoring.prometheus import metrics
from runners_manager.monitoring.prometheus import prometheus_metrics
from runners_manager.runner.RedisManager import RedisManager
from srcs.settings.yaml_config import EnvSettings, setup_settings
from web import cloud_manager
from web import github_manager
from web import runner_m
from web.models import CreateVm
from web.models import WebHook
from web.WebhookManager import WebHookManager

logger = logging.getLogger("runner_manager")
app = FastAPI()
app.mount("/static", StaticFiles(directory="templates/static"), name="static")
templates = Jinja2Templates(directory="templates/html")

app.add_route("/metrics", prometheus_metrics)


@lru_cache()
def get_args() -> EnvSettings:
    return EnvSettings()


@lru_cache()
def load_settings() -> dict:
    return setup_settings(get_args().setting_file)


@lru_cache()
def get_redis() -> RedisManager:
    args: EnvSettings = get_args()
    settings: dict = load_settings()
    r = Redis(
        host=settings["redis"]["host"],
        port=settings["redis"]["port"],
        password=args.redis_password,
    )
    return RedisManager(r)


@app.on_event("startup")
@repeat_every(seconds=60 * 60 * 2)
def delete_orphan_runners():
    """
    Delete Virtual Machine if there are not tracked by the runner manager and
    Delete Github Runner if there are not tracked as well
    """
    try:
        logger.info("list not tracked VM")
        gh_runners = [
            (elem["id"], elem["name"])
            for elem in github_manager.get_runners(runner_m.factory.runner_prefix)[
                "runners"
            ]
        ]
        server_list = cloud_manager.get_all_vms(runner_m.factory.runner_prefix)

        rd_runners = []
        for m in runner_m.runner_managers:
            rd_runners += m.get_runners().values()

        for server in server_list:
            if not next(filter(lambda r: r.vm_id == server.vm_id, rd_runners), None):
                logger.info(f"VM {server.vm_id} deleted")
                metrics.runner_vm_orphan_delete.labels(cloud=cloud_manager.name).inc()
                cloud_manager.delete_vm(server)

        for runner_id, runner_name in gh_runners:
            if not next(filter(lambda r: r.name == runner_name, rd_runners), None):
                logger.info(f"self-hosted {runner_name} deleted")
                metrics.runner_github_orphan_delete.labels(
                    cloud=cloud_manager.name
                ).inc()
                github_manager.force_delete_runner(runner_id)
    except Exception as e:
        logger.error(f"error type {type(e)}")
        logger.error(e)


# TODO: RELENG-6041 There could be an issue with this call when multiple
# runners are deployed
@app.on_event("startup")
@repeat_every(seconds=60 * 2)
def refresh():
    logger.info("Refresh runners")
    try:
        runners = github_manager.get_runners(runner_m.factory.runner_prefix)
        runner_m.update_all_runners(runners["runners"])
    except Exception as e:
        logger.error(e)


@app.on_event("startup")
@repeat_every(seconds=60 * 2)
def delete_images():
    cloud_manager.delete_images_from_shelved(f"runner-{github_manager.organization}")


# TODO: RELENG-6041 There could be an issue with this call when multiple
# runners are deployed
@app.post("/runners/refresh")
async def refresh_data():
    await refresh()
    return Response(status_code=200)


@app.post("/runners/reset")
async def reset_reset_runners(request: Request):
    """
    Delete Virutal machine and runner on github and create new runner
    """
    g_runners = github_manager.get_runners(runner_m.factory.runner_prefix)
    runner_m.update_all_runners(g_runners["runners"])
    runner_m.remove_all_runners()
    g_runners = github_manager.get_runners(runner_m.factory.runner_prefix)
    runner_m.update_all_runners(g_runners["runners"])
    return Response(status_code=200)


@app.post("/runners/create")
async def request_runners(params: CreateVm, request: Request):
    """
    Create VM
    """
    elem = next(
        filter(
            lambda runner_manager: runner_manager.vm_type.tags == params.tags,
            runner_m.runner_managers,
        )
    )

    if elem is None:
        return Response(status_code=404)
    for i in range(0, params.quantity):
        elem.create_runner()
    return Response(status_code=200)


@app.post("/runners/stop")
async def stop_runner(request: Request):
    runner_m.redis.set_manager_running(not runner_m.redis.get_manager_running())
    return Response(status_code=200)


@app.post("/webhook")
async def webhook_post(
    data: WebHook,
    request: Request,
    redis: RedisManager = Depends(get_redis),
):
    """
    Webhook point for Github
    """
    WebHookManager(redis, payload=data, event=request.headers["X-Github-Event"])()
    return Response(status_code=200)


@app.get("/", response_class=HTMLResponse)
async def main(request: Request):
    values = {
        "request": request,
        "runners": runner_m.runner_managers,
        "is_manager_running": runner_m.redis.get_manager_running(),
    }
    try:
        r = templates.TemplateResponse("index.html", values)
        return r
    except Exception as e:
        logger.info(e)
    return None


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "web.app:app", host="0.0.0.0", port=8080, debug=True, reload="/app/srcs"
    )
