from functools import lru_cache

from githubkit.webhooks import sign
from githubkit.webhooks.models import WorkflowJobCompleted
from hypothesis import given
from pytest import fixture

from runner_manager.dependencies import get_settings
from runner_manager.models.settings import Settings

from ..strategies import WorkflowJobCompletedStrategy


@lru_cache()
def settings():
    return Settings(
        github_webhook_secret="secret",
    )


@fixture()
def authentified_app(fastapp):
    fastapp.dependency_overrides[get_settings] = settings
    return fastapp


@given(workflow_job=WorkflowJobCompletedStrategy)
def test_workflow_job_event(workflow_job, client):
    assert workflow_job.action == "completed"
    response = client.post("/webhook", content=workflow_job.json(exclude_unset=True))
    assert response.status_code == 200


@given(workflow_job=WorkflowJobCompletedStrategy)
def test_workflow_job_hypothesis(workflow_job: WorkflowJobCompleted):
    assert workflow_job.action == "completed"


@given(workflow_job=WorkflowJobCompletedStrategy)
def test_webhook_authentication(workflow_job, client, authentified_app):
    data = workflow_job.json(exclude_unset=True)
    # First request without authentication
    response = client.post("/webhook/", content=data)
    assert response.status_code == 401
    # Second request with authentication
    signature = sign("secret", data, method="sha256")
    response = client.post(
        "/webhook/",
        content=data,
        headers={"X-Hub-Signature-256": signature, "X-GitHub-Event": "workflow_job"},
    )
    assert response.status_code == 200
