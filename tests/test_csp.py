"""Tests de la politique Content-Security-Policy."""

from app.utils.csp import build_content_security_policy


def test_csp_uses_nonce_and_disallows_unsafe_script_directives(app):
    """La CSP doit utiliser un nonce et interdire unsafe-inline/eval pour les scripts."""
    policy = build_content_security_policy(app, "test-nonce-value")

    assert "'nonce-test-nonce-value'" in policy
    assert "script-src" in policy
    assert "'unsafe-inline'" not in policy.split("script-src", 1)[1].split(";", 1)[0]
    assert "'unsafe-eval'" not in policy


def test_csp_response_header(client):
    """La réponse HTTP doit inclure une CSP durcie avec nonce."""
    response = client.get("/login")

    assert response.status_code == 200
    policy = response.headers.get("Content-Security-Policy", "")
    assert "script-src" in policy
    assert "'unsafe-inline'" not in policy.split("script-src", 1)[1].split(";", 1)[0]
    assert "'unsafe-eval'" not in policy
    assert "'nonce-" in policy
