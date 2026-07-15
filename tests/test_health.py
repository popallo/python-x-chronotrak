"""Tests de l'endpoint /health."""


def test_health_returns_minimal_payload(client):
    """La réponse publique ne doit pas exposer les détails internes."""
    response = client.get("/health")

    assert response.status_code == 200
    assert response.get_json() == {"status": "healthy"}


def test_health_returns_details_with_token(app, client):
    """Les détails internes sont disponibles uniquement avec le token configuré."""
    app.config["HEALTH_CHECK_TOKEN"] = "secret-health-token"

    response = client.get("/health", headers={"X-Health-Token": "secret-health-token"})

    assert response.status_code == 200
    data = response.get_json()
    assert data["status"] == "healthy"
    assert data["database"] == "ok"
    assert "email_queue_size" in data
    assert "email_worker_alive" in data
    assert "timestamp" in data


def test_health_hides_details_without_token(app, client):
    """Sans token valide, la réponse reste minimale même si HEALTH_CHECK_TOKEN est défini."""
    app.config["HEALTH_CHECK_TOKEN"] = "secret-health-token"

    response = client.get("/health")

    assert response.status_code == 200
    assert response.get_json() == {"status": "healthy"}
