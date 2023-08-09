from functools import lru_cache
from typing import Optional

from githubkit.webhooks import sign
from githubkit.webhooks.models import (
    InstallationLite,
    License,
    Organization,
    Repository,
    User,
    WorkflowJobCompleted,
    WorkflowJobCompletedPropWorkflowJob,
    WorkflowStepCompleted,
)
from hypothesis import given
from hypothesis import strategies as st
from pytest import fixture

from runner_manager.dependencies import get_settings
from runner_manager.models.settings import Settings


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
    WorkflowJobCompletedPropWorkflowJob, steps=st.lists(StepStrategy, max_size=1)
)


WorkflowJobStrategy = st.builds(
    WorkflowJobCompleted,
    action=st.just("completed"),
    repository=RepositoryStrategy,
    sender=UserStrategy,
    organization=st.builds(Organization),
    installation=st.builds(InstallationLite),
    workflow_job=JobPropStrategy,
)


@lru_cache()
def settings():
    return Settings(
        github_webhook_secret="secret",
    )


@fixture()
def authentified_app(fastapp):
    fastapp.dependency_overrides[get_settings] = settings
    return fastapp


@given(workflow_job=WorkflowJobStrategy)
def test_workflow_job_event(workflow_job, client):
    assert workflow_job.action == "completed"
    response = client.post("/webhook", content=workflow_job.json(exclude_unset=True))
    assert response.status_code == 200


@given(workflow_job=WorkflowJobStrategy)
def test_workflow_job_hypothesis(workflow_job: WorkflowJobCompleted):
    assert workflow_job.action == "completed"


@given(workflow_job=WorkflowJobStrategy)
def test_webhook_authentication(workflow_job, client, authentified_app):
    data = workflow_job.json(exclude_unset=True)
    # First request without authentication
    response = client.post("/webhook/", content=data)
    assert response.status_code == 401
    # Second request with authentication
    signature = sign("secret", data, method="sha256")
    response = client.post(
        "/webhook/", content=data, headers={"X-Hub-Signature-256": signature}
    )
    assert response.status_code == 200
