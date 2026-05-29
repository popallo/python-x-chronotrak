"""
Tests pour la suppression des saisies de temps (admin uniquement).
"""

import json

from app import db
from app.models.project import Project
from app.models.task import Task, TimeEntry


def _login(client, user):
    with client.session_transaction() as sess:
        sess["_user_id"] = str(user.id)
        sess["_fresh"] = True


def _create_task_with_time_entry(app, test_project, user, minutes=30):
    with app.app_context():
        project = db.session.merge(test_project)
        user = db.session.merge(user)

        task = Task(
            title="Tâche temps test",
            project_id=project.id,
            user_id=user.id,
            status="à faire",
            priority="normale",
            actual_minutes=minutes,
        )
        task.save()

        project.remaining_credit -= minutes
        entry = TimeEntry(task_id=task.id, user_id=user.id, minutes=minutes, description="Saisie test")
        db.session.add(entry)
        db.session.commit()
        db.session.refresh(task)
        db.session.refresh(entry)
        db.session.refresh(project)

        return task, entry, project


def test_delete_time_entry_admin_updates_counters(app, client, admin_user, test_project):
    """Un admin peut supprimer une saisie et les compteurs sont recalculés."""
    task, entry, project = _create_task_with_time_entry(app, test_project, admin_user, minutes=30)
    entry_id = entry.id
    task_id = task.id
    project_id = project.id
    task_slug = task.slug
    initial_credit = project.remaining_credit

    _login(client, admin_user)

    response = client.delete(
        f"/tasks/{task_slug}/time_entries/{entry_id}",
        headers={"Accept": "application/json", "X-Requested-With": "XMLHttpRequest"},
    )

    assert response.status_code == 200
    data = json.loads(response.data)
    assert data["success"] is True
    assert data["task"]["actual_time"] is None

    with app.app_context():
        assert db.session.get(TimeEntry, entry_id) is None
        task = db.session.get(Task, task_id)
        project = db.session.get(Project, project_id)
        assert task.actual_minutes is None
        assert project.remaining_credit == initial_credit + 30


def test_delete_time_entry_forbidden_for_technician(app, client, technician_user, test_project, admin_user):
    """Un technicien ne peut pas supprimer une saisie de temps."""
    task, entry, _ = _create_task_with_time_entry(app, test_project, admin_user, minutes=30)

    _login(client, technician_user)

    response = client.delete(
        f"/tasks/{task.slug}/time_entries/{entry.id}",
        headers={"Accept": "application/json", "X-Requested-With": "XMLHttpRequest"},
    )

    assert response.status_code == 403
    data = json.loads(response.data)
    assert data["success"] is False

    with app.app_context():
        assert db.session.get(TimeEntry, entry.id) is not None


def test_delete_time_entry_wrong_task_returns_404(app, client, admin_user, test_project):
    """Une entrée qui n'appartient pas à la tâche renvoie 404."""
    _task_a, entry_a, _ = _create_task_with_time_entry(app, test_project, admin_user, minutes=30)

    with app.app_context():
        project = db.session.merge(test_project)
        admin = db.session.merge(admin_user)
        task_b = Task(
            title="Autre tâche",
            project_id=project.id,
            user_id=admin.id,
            status="à faire",
            priority="normale",
        )
        task_b.save()
        task_b_slug = task_b.slug

    _login(client, admin_user)

    response = client.delete(
        f"/tasks/{task_b_slug}/time_entries/{entry_a.id}",
        headers={"Accept": "application/json", "X-Requested-With": "XMLHttpRequest"},
    )

    assert response.status_code == 404

    with app.app_context():
        assert db.session.get(TimeEntry, entry_a.id) is not None
