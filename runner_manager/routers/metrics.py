from typing import List

from fastapi import APIRouter
from fastapi.responses import PlainTextResponse
from prometheus_client import Gauge, generate_latest

from runner_manager import RunnerGroup
from runner_manager.models.runner import Runner

router = APIRouter(prefix="/metrics")

runners_count = Gauge("runners_count", "Number of runners", ["runner_group"])


@router.get("/", response_class=PlainTextResponse)
def compute_metrics() -> PlainTextResponse:
    groups: List[RunnerGroup] = RunnerGroup.find().all()
    for group in groups:
        runners: List[Runner] = group.get_runners()
        runners_count.labels(runner_group=group.name).set(len(runners))
    metrics = generate_latest().decode()
    return PlainTextResponse(content=metrics)
