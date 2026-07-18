"""Tests CSRF et endpoint pour la mise à jour de statut (kanban)."""

import re

from app import db
from app.models.task import Task


def _login(client, user):
    with client.session_transaction() as sess:
        sess["_user_id"] = str(user.id)
        sess["_fresh"] = True


def _create_task(app, test_project, admin_user):
    with app.app_context():
        project = db.session.merge(test_project)
        user = db.session.merge(admin_user)
        task = Task(
            title="Tâche statut test",
            project_id=project.id,
            user_id=user.id,
            status="à faire",
            priority="normale",
        )
        task.save()
        db.session.commit()
        db.session.refresh(task)
        return task


def test_update_status_without_csrf_returns_json_error(app, client, admin_user, test_project):
    """Sans token CSRF, l'appel AJAX doit recevoir une erreur JSON (pas une redirection HTML)."""
    app.config["WTF_CSRF_ENABLED"] = True
    app.config["WTF_CSRF_CHECK_DEFAULT"] = True

    task = _create_task(app, test_project, admin_user)
    _login(client, admin_user)

    response = client.post(
        "/tasks/update_status",
        json={"task_id": task.id, "status": "en cours"},
        headers={"Content-Type": "application/json"},
        follow_redirects=False,
    )

    assert response.status_code == 400
    assert "application/json" in response.headers.get("Content-Type", "")
    data = response.get_json()
    assert data["success"] is False
    assert "csrf" in data["error"].lower()


def test_update_status_with_csrf_header_succeeds(app, client, admin_user, test_project):
    """Avec header CSRF valide, le drag & drop doit mettre à jour le statut en JSON."""
    app.config["WTF_CSRF_ENABLED"] = True
    app.config["WTF_CSRF_CHECK_DEFAULT"] = True

    task = _create_task(app, test_project, admin_user)
    _login(client, admin_user)

    page = client.get(f"/tasks/{task.slug}")
    csrf_match = re.search(r'meta name="csrf-token" content="([^"]+)"', page.data.decode())
    assert csrf_match is not None
    csrf_token = csrf_match.group(1)

    response = client.post(
        "/tasks/update_status",
        json={"task_id": task.id, "status": "en cours"},
        headers={
            "Content-Type": "application/json",
            "X-CSRFToken": csrf_token,
        },
        follow_redirects=False,
    )

    assert response.status_code == 200
    data = response.get_json()
    assert data["success"] is True
    assert data["status"] == "en cours"


def test_kanban_button_slug_route_does_not_exist(app, client, admin_user, test_project):
    """L'ancienne URL /tasks/<slug>/update_status ne doit pas exister."""
    app.config["WTF_CSRF_ENABLED"] = True
    app.config["WTF_CSRF_CHECK_DEFAULT"] = True

    task = _create_task(app, test_project, admin_user)
    _login(client, admin_user)

    page = client.get(f"/tasks/{task.slug}")
    csrf_match = re.search(r'meta name="csrf-token" content="([^"]+)"', page.data.decode())
    assert csrf_match is not None

    response = client.post(
        f"/tasks/{task.slug}/update_status",
        json={"status": "en cours"},
        headers={
            "Content-Type": "application/json",
            "X-CSRFToken": csrf_match.group(1),
        },
        follow_redirects=False,
    )

    assert response.status_code == 404
