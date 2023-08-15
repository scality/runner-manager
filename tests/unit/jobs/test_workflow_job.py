from time import sleep
from uuid import uuid4

from githubkit.webhooks.models import (
    WorkflowJobCompleted,
    WorkflowJobInProgress,
    WorkflowJobQueued,
)
from hypothesis import assume, given, settings
from redis import Redis
from redis_om import JsonModel, Migrator
from rq import Queue
from rq.job import Job, JobStatus

from runner_manager import Settings
from runner_manager.jobs import workflow_job
from runner_manager.models.runner import Runner
from runner_manager.models.runner_group import RunnerGroup

from ...strategies import (
    QueueStrategy,
    RedisStrategy,
    SettingsStrategy,
    WorkflowJobCompletedStrategy,
    WorkflowJobInProgressStrategy,
    WorkflowJobQueuedStrategy,
)


def wait_for_migration(model: JsonModel):
    count = 0
    while model.find().count() == 0:
        print("waiting for index to be created")
        sleep(0.1)
        count += 1
        if count > 100:
            raise Exception("timeout waiting for index to be created")


def init_model(model: JsonModel, redis: Redis, settings: Settings):
    model.Meta.database = redis
    model.Meta.global_key_prefix = settings.name
    pks = model.all_pks()
    for pk in pks:
        model.delete(pk)
    Migrator().run()


@settings(max_examples=10)
@given(
    webhook=WorkflowJobCompletedStrategy,
    queue=QueueStrategy,
    settings=SettingsStrategy,
    redis=RedisStrategy,
)
def test_workflow_job_completed(
    webhook: WorkflowJobCompleted, queue: Queue, settings: Settings, redis: Redis
):
    init_model(RunnerGroup, redis, settings)
    init_model(Runner, redis, settings)
    assume(webhook.action == "completed")
    assert webhook.organization
    runner_group: RunnerGroup = RunnerGroup(
        organization=webhook.organization.login,
        name=webhook.workflow_job.runner_group_name,
        id=webhook.workflow_job.runner_group_id,
        labels=webhook.workflow_job.labels,
        manager=settings.name,
        backend={"name": "base"},
    )
    runner_group.save()
    runner: Runner = Runner(
        id=webhook.workflow_job.runner_id,
        name=webhook.workflow_job.runner_name,
        busy=False,
        status="online",
        manager=settings.name,
        runner_group_id=webhook.workflow_job.runner_group_id,
        runner_group_name=webhook.workflow_job.runner_group_name,
    )
    runner.save()

    Migrator().run()
    job: Job = queue.enqueue(workflow_job.completed, webhook)
    status: JobStatus = job.get_status()
    assert status == JobStatus.FINISHED
    assert (
        Runner.find(Runner.id == runner.id, Runner.manager == runner.manager).count()
        == 0
    )


@settings(max_examples=10)
@given(
    webhook=WorkflowJobInProgressStrategy,
    queue=QueueStrategy,
    settings=SettingsStrategy,
    redis=RedisStrategy,
)
def test_workflow_job_in_progress(
    webhook: WorkflowJobInProgress, queue: Queue, settings: Settings, redis: Redis
):

    # flush all keys that start with settings.name in redis

    init_model(RunnerGroup, redis, settings)
    init_model(Runner, redis, settings)
    assert webhook.organization
    runner_group: RunnerGroup = RunnerGroup(
        organization=webhook.organization.login,
        name=webhook.workflow_job.runner_group_name,
        id=webhook.workflow_job.runner_group_id,
        labels=webhook.workflow_job.labels,
        manager=settings.name,
        backend={"name": "base"},
    )
    runner_group.save()
    runner: Runner = Runner(
        id=webhook.workflow_job.runner_id,
        name=webhook.workflow_job.runner_name,
        busy=False,
        status="idle",
        manager=settings.name,
        runner_group_id=webhook.workflow_job.runner_group_id,
        runner_group_name=webhook.workflow_job.runner_group_name,
    )
    runner.save()
    Migrator().run()
    assert runner in Runner.find().all()
    assert runner_group in RunnerGroup.find().all()
    job: Job = queue.enqueue(workflow_job.in_progress, webhook)

    status: JobStatus = job.get_status()
    assert status == JobStatus.FINISHED
    assert (
        Runner.find(Runner.id == runner.id, Runner.manager == runner.manager).count()
        == 1
    )
    updated_runner: Runner = Runner.find(
        Runner.id == runner.id, Runner.manager == runner.manager
    ).first()
    assert updated_runner.busy is True
    assert updated_runner.status == "online"
    assert updated_runner.id == webhook.workflow_job.runner_id
    assert updated_runner.name == webhook.workflow_job.runner_name
    assert updated_runner.updated_at == webhook.workflow_job.started_at


@settings(max_examples=10)
@given(
    webhook=WorkflowJobQueuedStrategy,
    queue=QueueStrategy,
    settings=SettingsStrategy,
    redis=RedisStrategy,
)
def test_workflow_job_queued(
    webhook: WorkflowJobQueued, queue: Queue, settings: Settings, redis: Redis
):
    init_model(RunnerGroup, redis, settings)
    init_model(Runner, redis, settings)
    assert webhook.organization
    runner_group: RunnerGroup = RunnerGroup(
        organization=webhook.organization.login,
        name=uuid4().hex,
        labels=webhook.workflow_job.labels,
        manager=settings.name,
        backend={"name": "base"},
    )
    runner_group.save()
    Migrator().run()

    # wait for index to be created
    assert runner_group == RunnerGroup.get(runner_group.pk)

    wait_for_migration(RunnerGroup)
    job: Job = queue.enqueue(workflow_job.queued, webhook)
    status: JobStatus = job.get_status()
    assert status == JobStatus.FINISHED
    Migrator().run()

    wait_for_migration(Runner)
    assert (
        Runner.find(
            Runner.runner_group_name == runner_group.name,
            Runner.manager == settings.name,
        ).count()
        == 1
    )

    runner: Runner = Runner.find(
        Runner.runner_group_name == runner_group.name, Runner.manager == settings.name
    ).first()
    assert runner.busy is False
    assert runner.status == "offline"
