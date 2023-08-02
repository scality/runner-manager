def test_healthcheck(client):
    response = client.get("/_health")
    assert response.status_code == 200
