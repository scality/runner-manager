
from rq import Queue
from rq.job import Job, JobStatus
from typing import Optional
from hypothesis import given
from hypothesis import strategies as st
from githubkit.webhooks.types import WorkflowJobEvent
from runner_manager.jobs import workflow_job
from runner_manager.models.runner_group import RunnerGroup
from runner_manager.models.runner import Runner
from redis_om import Migrator, NotFoundError
from runner_manager.dependencies import get_queue

from pytest import raises

from githubkit.webhooks.models import (
    InstallationLite,
    License,
    Organization,
    Repository,
    User,
    WorkflowJobCompleted,
    WorkflowJobCompletedPropWorkflowJob,
    WorkflowJobInProgressPropWorkflowJob,
    WorkflowJobQueuedPropWorkflowJob,
    WorkflowStepCompleted,
)

# The method below is currently facing a KeyError on the license field
# license field is defined as an alias from license_ = Field(alias="license")
# RepositoryStrategy = st.builds(Repository,
#     license_=st.builds(License)
# )
class Repo(Repository):
    license: Optional[License] = None


UserStrategy = st.builds(
    User,
    name=st.just("test"),
    email=st.just("test@email.com"),
)
RepositoryStrategy = st.builds(
    Repo,
    license=st.just(None),
    owner=UserStrategy,
)

StepStrategy = st.builds(WorkflowStepCompleted)

JobPropStrategy = st.builds(
    WorkflowJobCompletedPropWorkflowJob,
    steps=st.lists(StepStrategy, max_size=1),
    runner_name=st.text(min_size=1, max_size=10),
    runner_id=st.integers(min_value=1),
    runner_group_name=st.text(min_size=1, max_size=10),
    runner_group_id=st.integers(min_value=1),
    labels=st.lists(st.text(min_size=1, max_size=10)),
)


WorkflowJobStrategy = st.builds(
    WorkflowJobCompleted,
    action=st.just("completed"),
    repository=RepositoryStrategy,
    workflow_job=JobPropStrategy,
)

@given(webhook=WorkflowJobStrategy)
def test_workflow_job(webhook: WorkflowJobCompleted, queue: Queue):
    print(webhook.workflow_job.runner_group_name)
    runner_group: RunnerGroup = RunnerGroup(
        name=webhook.workflow_job.runner_group_name,
        id=webhook.workflow_job.runner_group_id,
        labels=webhook.workflow_job.labels,
        backend={"name": "base"}
    )
    runner_group.save()
    runner: Runner = Runner(
        id=webhook.workflow_job.runner_id,
        name=webhook.workflow_job.runner_name,
        busy=False,
        status="online",
        runner_group_id=runner_group.id,
    )
    runner.save()
    Migrator().run()
    job: Job = queue.enqueue(workflow_job.completed, webhook)
    status: JobStatus = job.get_status()
    assert status == JobStatus.FINISHED
    with raises(NotFoundError):
        Runner.get(runner.pk)

