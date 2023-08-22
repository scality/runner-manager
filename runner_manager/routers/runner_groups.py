from typing import Dict, List

from fastapi import APIRouter, Depends, HTTPException
from redis_om import NotFoundError
from rq import Queue
from rq.job import Job

from runner_manager import RunnerGroup, Settings
from runner_manager.clients.github import GitHub
from runner_manager.dependencies import get_github, get_queue, get_settings
from runner_manager.jobs.healthcheck import group as group_healthcheck
from runner_manager.jobs.reset import group as group_reset
from runner_manager.models.api import JobResponse

router = APIRouter(prefix="/groups")


@router.get("/")
def list() -> List[RunnerGroup]:
    return RunnerGroup.find().all()


@router.get("/{name}")
def get(name: str) -> RunnerGroup:
    try:
        return RunnerGroup.find(RunnerGroup.name == name).first()
    except NotFoundError:
        raise HTTPException(status_code=404, detail=f"Runner group {name} not found.")


@router.delete("/{name}")
def delete(name: str, github: GitHub = Depends(get_github)) -> Dict[str, str]:
    try:
        group = RunnerGroup.find(RunnerGroup.name == name).first()
        group.delete(pk=group.pk, github=github)
        return {"message": f"Runner group {name} deleted."}
    except NotFoundError:
        raise HTTPException(status_code=404, detail=f"Runner group {name} not found.")


@router.post("/{name}/healthcheck")
def healthcheck(
    name: str,
    queue: Queue = Depends(get_queue),
    settings: Settings = Depends(get_settings),
) -> JobResponse:
    try:
        group = RunnerGroup.find(RunnerGroup.name == name).first()
        job: Job = queue.enqueue(
            group_healthcheck, group.pk, settings.time_to_live, settings.timeout_runner
        )
        return JobResponse(id=job.id, status=job.get_status())
    except NotFoundError:
        raise HTTPException(status_code=404, detail=f"Runner group {name} not found.")


@router.post("/{name}/reset")
def reset(
    name: str,
    queue: Queue = Depends(get_queue),
) -> JobResponse:
    try:
        group = RunnerGroup.find(RunnerGroup.name == name).first()
        job: Job = queue.enqueue(group_reset, group.pk)
        return JobResponse(id=job.id, status=job.get_status())
    except NotFoundError:
        raise HTTPException(status_code=404, detail=f"Runner group {name} not found.")
