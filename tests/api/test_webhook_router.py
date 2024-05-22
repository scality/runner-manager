from functools import lru_cache

from githubkit.versions.latest.models import (
    WebhookWorkflowJobCompleted as WorkflowJobCompleted,
)
from githubkit.webhooks import sign
from hypothesis import given
from pytest import fixture
from rq import Queue

from runner_manager.dependencies import get_settings
from runner_manager.models.settings import Settings

from ..strategies import PingStrategy, WorkflowJobCompletedStrategy


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
    data = workflow_job.json(exclude_unset=True)
    # Send request without X-GitHub-Event header should return 200
    # but success should be False
    response = client.post("/webhook", content=data)
    assert response.status_code == 200
    assert response.json()["success"] is False
    response = client.post(
        "/webhook", content=data, headers={"X-GitHub-Event": "workflow_job"}
    )
    assert response.status_code == 200
    assert response.json()["success"] is True


@given(workflow_job=WorkflowJobCompletedStrategy)
def test_workflow_job_hypothesis(workflow_job: WorkflowJobCompleted):
    assert workflow_job.action == "completed"


@given(workflow_job=WorkflowJobCompletedStrategy)
def test_webhook_retry_job(workflow_job, client, queue: Queue):
    assert workflow_job.action == "completed"
    data = workflow_job.json(exclude_unset=True)
    response = client.post(
        "/webhook/", content=data, headers={"X-GitHub-Event": "workflow_job"}
    )
    assert response.status_code == 200
    job_id = response.json()["job_id"]
    job = queue.fetch_job(job_id)
    assert job is not None
    assert job.retries_left == 3


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

    # Third request with incorrect authentication
    signature = sign("wrong_secret", data, method="sha256")
    response = client.post(
        "/webhook/",
        content=data,
        headers={"X-Hub-Signature-256": signature, "X-GitHub-Event": "workflow_job"},
    )
    assert response.status_code == 401


@given(ping=PingStrategy)
def test_ping_event(ping, client):
    response = client.post("/webhook", content=ping.json(exclude_unset=True))
    assert response.status_code == 200
