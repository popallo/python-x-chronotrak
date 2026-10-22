"""Tests CSRF et endpoint pour le sous-statut d'attente des tâches."""

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
            title="Tâche waiting status test",
            project_id=project.id,
            user_id=user.id,
            status="à faire",
            priority="normale",
        )
        task.save()
        db.session.commit()
        db.session.refresh(task)
        return task


def _csrf_token(client, task):
    page = client.get(f"/tasks/{task.slug}")
    csrf_match = re.search(r'meta name="csrf-token" content="([^"]+)"', page.data.decode())
    assert csrf_match is not None
    return csrf_match.group(1)


def test_update_waiting_status_without_csrf_returns_json_error(app, client, admin_user, test_project):
    """Sans token CSRF, l'appel AJAX doit recevoir une erreur JSON."""
    app.config["WTF_CSRF_ENABLED"] = True
    app.config["WTF_CSRF_CHECK_DEFAULT"] = True

    task = _create_task(app, test_project, admin_user)
    _login(client, admin_user)

    response = client.post(
        "/tasks/update_waiting_status",
        json={"task_id": task.id, "waiting_status": "attente information"},
        headers={"Content-Type": "application/json"},
        follow_redirects=False,
    )

    assert response.status_code == 400
    assert "application/json" in response.headers.get("Content-Type", "")
    data = response.get_json()
    assert data["success"] is False
    assert "csrf" in data["error"].lower()


def test_update_waiting_status_with_csrf_header_succeeds(app, client, admin_user, test_project):
    """Avec header CSRF valide, le sous-statut doit être mis à jour."""
    app.config["WTF_CSRF_ENABLED"] = True
    app.config["WTF_CSRF_CHECK_DEFAULT"] = True

    task = _create_task(app, test_project, admin_user)
    _login(client, admin_user)
    csrf_token = _csrf_token(client, task)

    response = client.post(
        "/tasks/update_waiting_status",
        json={"task_id": task.id, "waiting_status": "attente validation client"},
        headers={
            "Content-Type": "application/json",
            "X-CSRFToken": csrf_token,
        },
        follow_redirects=False,
    )

    assert response.status_code == 200
    data = response.get_json()
    assert data["success"] is True
    assert data["waiting_status"] == "attente validation client"
    assert data["waiting_status_label"] == "Attente validation client"

    with app.app_context():
        refreshed = db.session.get(Task, task.id)
        assert refreshed.waiting_status == "attente validation client"


def test_clear_waiting_status_with_empty_value(app, client, admin_user, test_project):
    """Une valeur vide doit effacer le sous-statut d'attente."""
    app.config["WTF_CSRF_ENABLED"] = True
    app.config["WTF_CSRF_CHECK_DEFAULT"] = True

    task = _create_task(app, test_project, admin_user)
    with app.app_context():
        db_task = db.session.get(Task, task.id)
        db_task.waiting_status = "bloqué"
        db.session.commit()

    _login(client, admin_user)
    csrf_token = _csrf_token(client, task)

    response = client.post(
        "/tasks/update_waiting_status",
        json={"task_id": task.id, "waiting_status": ""},
        headers={
            "Content-Type": "application/json",
            "X-CSRFToken": csrf_token,
        },
        follow_redirects=False,
    )

    assert response.status_code == 200
    data = response.get_json()
    assert data["success"] is True
    assert data["waiting_status"] is None

    with app.app_context():
        refreshed = db.session.get(Task, task.id)
        assert refreshed.waiting_status is None


def test_invalid_waiting_status_rejected(app, client, admin_user, test_project):
    """Une valeur hors liste fixe doit être rejetée."""
    app.config["WTF_CSRF_ENABLED"] = True
    app.config["WTF_CSRF_CHECK_DEFAULT"] = True

    task = _create_task(app, test_project, admin_user)
    _login(client, admin_user)
    csrf_token = _csrf_token(client, task)

    response = client.post(
        "/tasks/update_waiting_status",
        json={"task_id": task.id, "waiting_status": "valeur inventée"},
        headers={
            "Content-Type": "application/json",
            "X-CSRFToken": csrf_token,
        },
        follow_redirects=False,
    )

    assert response.status_code == 400
    data = response.get_json()
    assert data["success"] is False


def test_task_detail_includes_waiting_status_buttons(app, client, admin_user, test_project):
    """La page détail doit exposer les boutons de sous-statut d'attente sous le statut."""
    task = _create_task(app, test_project, admin_user)
    _login(client, admin_user)

    page = client.get(f"/tasks/{task.slug}")
    html = page.data.decode()
    assert page.status_code == 200
    assert "waiting-status-toggle" in html
    assert "waiting-status-btn" in html
    assert 'data-waiting-status="attente validation client"' in html
    assert 'data-waiting-status="attente information"' in html
