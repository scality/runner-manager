from typing import Optional
from uuid import uuid4

from githubkit.webhooks.models import (
    License,
    Repository,
    User,
    WorkflowJobCompleted,
    WorkflowJobCompletedPropWorkflowJob,
    WorkflowJobInProgress,
    WorkflowJobQueued,
    WorkflowStepCompleted,
)
from githubkit.webhooks.types import WorkflowJobEvent
from hypothesis import assume, given
from hypothesis import strategies as st
from pytest import raises
from redis_om import Migrator, NotFoundError
from rq import Queue
from rq.job import Job, JobStatus

from runner_manager.models.runner import Runner
from runner_manager.models.runner_group import RunnerGroup


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


WorkflowJobCompletedStrategy = st.builds(
    WorkflowJobCompleted,
    action=st.just("completed"),
    repository=RepositoryStrategy,
)

WorkflowJobQueuedStrategy = st.builds(
    WorkflowJobQueued,
    action=st.just("queued"),
    repository=RepositoryStrategy,
)

WorkflowJobInProgressStrategy = st.builds(
    WorkflowJobInProgress,
    action=st.just("in_progress"),
    repository=RepositoryStrategy,
)


@given(
    webhook=st.one_of(
        WorkflowJobCompletedStrategy,
        WorkflowJobQueuedStrategy,
        WorkflowJobInProgressStrategy,
    )
)
def test_workflow_job(webhook: WorkflowJobEvent, queue: Queue):
    runner_group_name: str = webhook.workflow_job.runner_group_name
    if webhook.action != "queued":
        assume(webhook.workflow_job.runner_group_name is not None)
        runner: Runner = Runner(
            id=webhook.workflow_job.runner_id,
            name=webhook.workflow_job.runner_name,
            busy=False,
            status="online",
            runner_group_id=webhook.workflow_job.runner_group_id,
        )
        runner.save()
    else:
        runner_group_name = str(uuid4())
    runner_group: RunnerGroup = RunnerGroup(
        name=runner_group_name,
        id=webhook.workflow_job.runner_group_id,
        labels=webhook.workflow_job.labels,
        backend={"name": "base"},
    )
    runner_group.save()

    Migrator().run()
    job: Job = queue.enqueue(
        f"runner_manager.jobs.workflow_job.{webhook.action}", webhook
    )
    status: JobStatus = job.get_status()
    assert status == JobStatus.FINISHED
    if webhook.action != "queued":
        with raises(NotFoundError):
            Runner.get(runner.pk)
    else:
        assert Runner.find(Runner.runner_group_id == runner_group.id).count() == 1
