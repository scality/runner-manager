from __future__ import annotations

from string import ascii_lowercase
from typing import Optional

from githubkit.versions.latest.models import JobPropStepsItems as WorkflowStepCompleted
from githubkit.versions.latest.models import (
    License,
    Organization,
    Repository,
    RepositoryPropPermissions,
)
from githubkit.versions.latest.models import Runner as GitHubRunner
from githubkit.versions.latest.models import SimpleUser as User
from githubkit.versions.latest.models import WebhookPing, WebhookPingPropHook
from githubkit.versions.latest.models import (
    WebhookWorkflowJobCompleted as WorkflowJobCompleted,
)
from githubkit.versions.latest.models import (
    WebhookWorkflowJobCompletedPropWorkflowJob as WorkflowJobCompletedPropWorkflowJob,
)
from githubkit.versions.latest.models import (
    WebhookWorkflowJobInProgress as WorkflowJobInProgress,
)
from githubkit.versions.latest.models import (
    WebhookWorkflowJobInProgressPropWorkflowJob as WorkflowJobInProgressPropWorkflowJob,
)
from githubkit.versions.latest.models import (
    WebhookWorkflowJobQueued as WorkflowJobQueued,
)
from githubkit.versions.latest.models import (
    WebhookWorkflowJobQueuedPropWorkflowJob as WorkflowJobQueuedPropWorkflowJob,
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


# Text strategy with only ascii characters
# that must start with a alphabetic character,
# and only lowercase characters
Text = st.text(ascii_lowercase, min_size=10, max_size=10).filter(
    lambda x: x[0].isalpha()
)
Int = st.integers(min_value=1, max_value=100)
UserStrategy = st.builds(
    User,
    name=st.just("test"),
    email=st.just("test@email.com"),
)
RepoPermission = st.builds(
    RepositoryPropPermissions,
    admin=st.just(True),
    push=st.just(True),
    pull=st.just(True),
    maintain=st.just(True),
    triage=st.just(True),
)
RepositoryStrategy = st.builds(
    Repo,
    license=st.just(None),
    owner=UserStrategy,
    merge_commit_title=st.just("PR_TITLE"),
    squash_merge_commit_message=st.just("PR_BODY"),
    use_squash_pr_title_as_default=st.just(True),
    allow_update_branch=st.just(True),
    delete_branch_on_merge=st.just(True),
    allow_auto_merge=st.just(True),
    allow_rebase_merge=st.just(True),
    allow_squash_merge=st.just(True),
    topics=st.just(["topic"]),
    is_template=st.just(False),
    has_discussions=st.just(True),
    squash_merge_commit_title=st.just("PR_TITLE"),
    merge_commit_message=st.just("PR_BODY"),
    allow_merge_commit=st.just(True),
    allow_forking=st.just(False),
    web_commit_signoff_required=st.just(False),
    anonymous_access_enabled=st.just(False),
    permissions=RepoPermission,
)

OrgStrategy = st.builds(
    Organization,
    login=st.just("octo-org"),
)

StepStrategy = st.builds(
    WorkflowStepCompleted,
    status=st.just("completed"),
    conclusion=st.just("success"),
    name=st.just("step"),
    number=st.just(42),
    started_at=st.just(None),
    completed_at=st.just(None),
)

JobPropCompletedStrategy = st.builds(
    WorkflowJobCompletedPropWorkflowJob,
    steps=st.lists(StepStrategy, max_size=1),
    runner_name=Text,
    runner_id=Int,
    status=st.just("completed"),
    runner_group_name=Text,
    runner_group_id=Int,
    labels=st.lists(Text, min_size=1, max_size=5),
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
    github_base_url=st.just("http://localhost:4010"),
    github_token=st.just("test"),
    time_to_live=st.integers(1, 60),
    timeout_runner=st.integers(120, 600),
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
    WebhookPingPropHook,
    events=st.just(["*"]),
)

GithubRunnerStrategy = st.builds(
    GitHubRunner,
    id=st.integers(),
    status=st.sampled_from(["online", "offline"]),
    busy=st.booleans(),
    name=Text,
)
PingStrategy = st.builds(WebhookPing, hook=PingHookStrategy)
