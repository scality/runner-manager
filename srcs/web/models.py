from datetime import datetime
from typing import List
from typing import Optional

from pydantic import BaseModel

"""
This file contain basic webhook event data models
"""


class WorkflowRun(BaseModel):
    id: int
    name: str
    event: str
    status: str
    conclusion: Optional[str] = None
    head_sha: str
    workflow_id: int
    run_number: int
    head_branch: str
    created_at: datetime
    updated_at: datetime or None


class WorkflowJob(BaseModel):
    id: int
    name: str
    status: str
    conclusion: Optional[str] = None
    head_sha: str
    run_attempt: int
    labels: List[str]

    # Information about the runner can be null if the Job is queued
    runner_id: Optional[int] = None
    runner_name: Optional[str] = None
    runner_group_id: Optional[int] = None
    runner_group_name: Optional[str] = None


class Repository(BaseModel):
    name: str
    full_name: str


class WebHook(BaseModel):
    action: str
    workflow_job: Optional[WorkflowJob] = None
    workflow_run: Optional[WorkflowRun] = None
    repository: Repository


class CreateVm(BaseModel):
    tags: [str]
    quantity: int
