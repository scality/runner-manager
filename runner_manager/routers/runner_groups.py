from typing import Dict, List

from fastapi import APIRouter, Depends, HTTPException
from redis_om import NotFoundError

from runner_manager import RunnerGroup
from runner_manager.clients.github import GitHub
from runner_manager.dependencies import get_github

router = APIRouter(prefix="/groups")


@router.get("/")
def get() -> List[str]:
    groups = RunnerGroup.find().all()
    return [group.name for group in groups]


@router.delete("/{group_name}")
def delete(group_name: str, github: GitHub = Depends(get_github)) -> Dict[str, str]:
    try:
        group = RunnerGroup.find(RunnerGroup.name == group_name).first()
        group.delete(pk=group.pk, github=github)
        return {"message": f"Runner group {group_name} deleted."}
    except NotFoundError:
        raise HTTPException(
            status_code=404, detail=f"Runner group {group_name} not found."
        )
