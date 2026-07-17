"""Tests CSRF pour le clonage de tâche."""

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
            title="Tâche à cloner",
            project_id=project.id,
            user_id=user.id,
            status="à faire",
            priority="normale",
        )
        task.save()
        db.session.commit()
        db.session.refresh(task)
        return task


def test_clone_task_page_includes_csrf_token(app, client, admin_user, test_project):
    """La modale de clonage doit inclure un token CSRF dans le formulaire."""
    app.config["WTF_CSRF_ENABLED"] = True
    app.config["WTF_CSRF_CHECK_DEFAULT"] = True

    task = _create_task(app, test_project, admin_user)
    _login(client, admin_user)

    response = client.get(f"/tasks/{task.slug}")
    html = response.data.decode()

    assert response.status_code == 200
    assert 'action="/tasks/' in html and "/clone" in html
    assert re.search(
        r'<form[^>]*action="[^"]*/tasks/[^"]*/clone"[^>]*>.*?name="csrf_token"[^>]*value="([^"]+)"',
        html,
        re.DOTALL,
    )


def test_clone_task_post_without_csrf_redirects_with_session_message(app, client, admin_user, test_project):
    """Un POST clone sans token CSRF doit être rejeté et rediriger vers la tâche."""
    app.config["WTF_CSRF_ENABLED"] = True
    app.config["WTF_CSRF_CHECK_DEFAULT"] = True

    task = _create_task(app, test_project, admin_user)
    _login(client, admin_user)

    response = client.post(
        f"/tasks/{task.slug}/clone",
        data={"clone_checklist": "1"},
        follow_redirects=True,
    )

    body = response.data.decode()
    assert response.status_code == 200
    assert "session a expiré" in body.lower()


def test_clone_task_post_with_csrf_succeeds(app, client, admin_user, test_project):
    """Un POST clone avec token CSRF valide doit créer la copie."""
    app.config["WTF_CSRF_ENABLED"] = True
    app.config["WTF_CSRF_CHECK_DEFAULT"] = True

    task = _create_task(app, test_project, admin_user)
    _login(client, admin_user)

    detail_page = client.get(f"/tasks/{task.slug}")
    html = detail_page.data.decode()
    csrf_match = re.search(
        r'<form[^>]*action="[^"]*/tasks/[^"]*/clone"[^>]*>.*?name="csrf_token"[^>]*value="([^"]+)"',
        html,
        re.DOTALL,
    )
    assert csrf_match is not None

    response = client.post(
        f"/tasks/{task.slug}/clone",
        data={"clone_checklist": "1", "csrf_token": csrf_match.group(1)},
        follow_redirects=False,
    )

    assert response.status_code == 302
    assert "session a expiré" not in response.data.decode().lower()
