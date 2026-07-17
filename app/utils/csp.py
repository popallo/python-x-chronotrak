"""Construction de la politique Content-Security-Policy."""

from flask import Flask


def build_content_security_policy(app: Flask, nonce: str) -> str:
    """Construit l'en-tête CSP avec un nonce pour les scripts inline autorisés."""
    script_src = (
        f"'self' 'nonce-{nonce}' "
        "https://cdn.jsdelivr.net https://code.jquery.com "
        "https://*.cloudflare.com https://*.cloudflareinsights.com"
    )
    style_src = "'self' 'unsafe-inline' https://cdn.jsdelivr.net https://cdnjs.cloudflare.com"

    if app.config.get("FLASK_ENV") == "development":
        script_src += " http://localhost:5000 http://127.0.0.1:5000"

    return (
        "default-src 'self' https://*.cloudflare.com https://*.cloudflareinsights.com; "
        f"script-src {script_src}; "
        f"style-src {style_src}; "
        "font-src 'self' https://cdn.jsdelivr.net https://cdnjs.cloudflare.com; "
        "img-src 'self' data: https:; "
        "connect-src 'self' https://cdn.jsdelivr.net https://code.jquery.com "
        "https://*.cloudflare.com https://*.cloudflareinsights.com; "
        "frame-src 'self' https://*.cloudflare.com; "
        "worker-src 'self'"
    )
