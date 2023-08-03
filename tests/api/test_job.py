import pytest

#@pytest.fixture
#def webhook():
#    return {
#        "repository": {
#            "name": "repo",
#            "full_name": "org/repo",
#            "visibility": "private",
#        }
#    }

def test_webhook_job_endpoint(client):
    headers = {"X-GitHub-Event": "push"}
    webhook = {
        "repository": {
            "name": "repo",
            "full_name": "org/repo",
            "visibility": "private",
        }
    }
    response = client.post("/webhook", json=webhook, headers=headers)

    assert response.status_code == 200

def test_get_webhook(client):
    response = client.get("/webhook")
    assert response.status_code == 200
