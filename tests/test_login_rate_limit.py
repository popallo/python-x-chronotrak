"""Tests de la limitation des tentatives de connexion."""

from app import db
from app.models.user import User
from app.utils.login_rate_limit import clear_login_attempts, is_login_rate_limited, record_failed_login


def test_login_rate_limit_blocks_after_max_attempts(app):
    """Bloque les connexions après le nombre maximal de tentatives."""
    app.config["LOGIN_RATE_LIMIT_ENABLED"] = True
    app.config["LOGIN_RATE_LIMIT_MAX_ATTEMPTS"] = 3
    app.config["LOGIN_RATE_LIMIT_WINDOW"] = 900

    with app.app_context():
        client_ip = "203.0.113.10"
        assert is_login_rate_limited(client_ip) is False

        record_failed_login(client_ip)
        record_failed_login(client_ip)
        assert is_login_rate_limited(client_ip) is False

        record_failed_login(client_ip)
        assert is_login_rate_limited(client_ip) is True


def test_login_rate_limit_clears_after_success(app):
    """Réinitialise le compteur après une connexion réussie."""
    app.config["LOGIN_RATE_LIMIT_ENABLED"] = True
    app.config["LOGIN_RATE_LIMIT_MAX_ATTEMPTS"] = 2

    with app.app_context():
        client_ip = "203.0.113.11"
        record_failed_login(client_ip)
        record_failed_login(client_ip)
        assert is_login_rate_limited(client_ip) is True

        clear_login_attempts(client_ip)
        assert is_login_rate_limited(client_ip) is False


def test_login_route_returns_rate_limit_message(app, client):
    """La route de connexion affiche un message lorsque la limite est atteinte."""
    app.config["LOGIN_RATE_LIMIT_ENABLED"] = True
    app.config["LOGIN_RATE_LIMIT_MAX_ATTEMPTS"] = 1
    app.config["WTF_CSRF_ENABLED"] = False

    with app.app_context():
        user = User(name="Rate Limit", email="ratelimit@test.com", role="admin")
        user.set_password("correct-password")
        db.session.add(user)
        db.session.commit()

    client.post("/login", data={"email": "ratelimit@test.com", "password": "wrong-password"})
    response = client.post("/login", data={"email": "ratelimit@test.com", "password": "wrong-password"})

    assert response.status_code == 200
    assert b"Trop de tentatives de connexion" in response.data
