from string import ascii_letters
from typing import Optional

from githubkit.webhooks.models import (
    License,
    Organization,
    PingEvent,
    PingEventPropHook,
    Repository,
    User,
    WorkflowJobCompleted,
    WorkflowJobCompletedPropWorkflowJob,
    WorkflowJobInProgress,
    WorkflowJobInProgressPropWorkflowJob,
    WorkflowJobQueued,
    WorkflowJobQueuedPropWorkflowJob,
    WorkflowStepCompleted,
)
from hypothesis import strategies as st
from redis import Redis
from rq import Queue

from runner_manager import Settings


# The method below is currently facing a KeyError on the license field
# license field is defined as an alias from license_ = Field(alias="license")
# RepositoryStrategy = st.builds(Repository,
#     license_=st.builds(License)
# )
class Repo(Repository):
    license: Optional[License] = None


# Text strategy with only normal characters
Text = st.text(ascii_letters, min_size=10, max_size=10)
Int = st.integers(min_value=1, max_value=100)
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

OrgStrategy = st.builds(
    Organization,
    login=st.just("octo-org"),
)

StepStrategy = st.builds(WorkflowStepCompleted)

JobPropCompletedStrategy = st.builds(
    WorkflowJobCompletedPropWorkflowJob,
    steps=st.lists(StepStrategy, max_size=1),
    runner_name=Text,
    runner_id=Int,
    status=st.just("completed"),
    runner_group_name=Text,
    runner_group_id=Int,
    labels=st.lists(Text, min_size=1, max_size=5),
    started_at=st.datetimes(),
)

JobPropInProgressStrategy = st.builds(
    WorkflowJobInProgressPropWorkflowJob,
    steps=st.lists(StepStrategy, max_size=1),
    runner_name=Text,
    runner_id=Int,
    status=st.just("in_progress"),
    runner_group_name=Text,
    runner_group_id=Int,
    labels=st.lists(Text, min_size=1, max_size=5),
    started_at=st.datetimes(),
)

JobPropQueuedStrategy = st.builds(
    WorkflowJobQueuedPropWorkflowJob,
    steps=st.lists(StepStrategy, max_size=1),
    runner_name=Text,
    runner_id=Int,
    status=st.just("queued"),
    runner_group_name=st.none(),
    runner_group_id=st.none(),
    labels=st.lists(Text, min_size=1, max_size=5),
)

WorkflowJobCompletedStrategy = st.builds(
    WorkflowJobCompleted,
    action=st.just("completed"),
    repository=RepositoryStrategy,
    sender=UserStrategy,
    organization=OrgStrategy,
    workflow_job=JobPropCompletedStrategy,
)

WorkflowJobQueuedStrategy = st.builds(
    WorkflowJobQueued,
    action=st.just("queued"),
    repository=RepositoryStrategy,
    sender=UserStrategy,
    organization=OrgStrategy,
    workflow_job=JobPropQueuedStrategy,
)

WorkflowJobInProgressStrategy = st.builds(
    WorkflowJobInProgress,
    action=st.just("in_progress"),
    repository=RepositoryStrategy,
    sender=UserStrategy,
    organization=OrgStrategy,
    workflow_job=JobPropInProgressStrategy,
)

SettingsStrategy = st.builds(
    Settings,
    name=Text,
    redis_om_url=st.just("redis://localhost:6379/0"),
)

RedisStrategy = st.builds(
    Redis,
    host=st.just("localhost"),
    port=st.just(6379),
    db=st.just(0),
    decode_responses=st.just(True),
)

QueueStrategy = st.builds(
    Queue,
    connection=RedisStrategy,
    is_async=st.just(False),
)

PingHookStrategy = st.builds(
    PingEventPropHook,
    events=st.just(["*"]),
)

PingStrategy = st.builds(PingEvent, hook=PingHookStrategy)
