"""Tests du flux CSRF sur la connexion."""

import re


def test_login_page_exposes_csrf_token_in_meta(app, client):
    """La page de connexion doit exposer un token CSRF valide dans la meta."""
    app.config["WTF_CSRF_ENABLED"] = True
    app.config["WTF_CSRF_CHECK_DEFAULT"] = True

    response = client.get("/login")

    assert response.status_code == 200
    match = re.search(r'meta name="csrf-token" content="([^"]+)"', response.data.decode())
    assert match is not None
    assert match.group(1)


def test_login_post_with_session_succeeds_csrf(app, client, admin_user):
    """Un POST login avec cookie de session et token CSRF doit passer la validation."""
    app.config["WTF_CSRF_ENABLED"] = True
    app.config["WTF_CSRF_CHECK_DEFAULT"] = True

    login_page = client.get("/login")
    html = login_page.data.decode()
    csrf_match = re.search(r'name="csrf_token"[^>]*value="([^"]+)"', html)
    assert csrf_match is not None

    response = client.post(
        "/login",
        data={
            "email": admin_user.email,
            "password": "testpassword",
            "csrf_token": csrf_match.group(1),
        },
        follow_redirects=False,
    )

    assert response.status_code == 302
    assert "Oups" not in response.data.decode()


def test_csrf_error_redirects_to_login_instead_of_error_page(app, client):
    """Une erreur CSRF ne doit pas afficher la page d'erreur générique."""
    app.config["WTF_CSRF_ENABLED"] = True
    app.config["WTF_CSRF_CHECK_DEFAULT"] = True

    response = client.post(
        "/login",
        data={"email": "someone@example.com", "password": "wrong"},
        follow_redirects=True,
    )

    assert response.status_code == 200
    body = response.data.decode()
    assert "Oups" not in body
    assert "session a expiré" in body.lower() or "Connexion" in body
