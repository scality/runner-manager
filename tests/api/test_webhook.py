def test_get_webhook(client):
    response = client.get("/webhook")
    assert response.status_code == 200
