import json
from datetime import UTC, datetime, timedelta

from app import db
from app.forms.task import CommentForm, DeleteTaskForm, EditCommentForm, TaskForm, TimeEntryForm
from app.models.project import Project
from app.models.task import ChecklistItem, Comment, Task, TaskRecurrenceSeries, TimeEntry, UserPinnedTask
from app.models.user import User
from app.utils import get_utc_now
from app.utils.decorators import login_and_client_required
from app.utils.route_utils import (
    delete_from_db,
    get_project_by_slug_or_id,
    get_task_by_slug_or_id,
    save_to_db,
)
from flask import Blueprint, current_app, flash, jsonify, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from sqlalchemy import func


def _today_utc_date():
    return get_utc_now().date()


def _delete_future_recurrence_instances(series_id: int, keep_task_id: int | None = None):
    """
    Supprime les occurrences futures (planifiées dans le futur) d'une série.
    On reste conservateur: on ne supprime que les tâches "à faire" sans temps passé.
    """
    today = _today_utc_date()
    q = Task.query.filter(
        Task.recurrence_series_id == series_id,
        Task.scheduled_for.isnot(None),
        Task.scheduled_for > today,
        Task.status == "à faire",
        Task.is_archived == False,
    )
    if keep_task_id:
        q = q.filter(Task.id != keep_task_id)

    tasks_to_delete = q.all()
    for t in tasks_to_delete:
        if t.time_entries:
            # sécurité: ne pas supprimer si du temps a été enregistré
            continue
        db.session.delete(t)


def _ensure_recurrence_instances(template_task: Task, series: TaskRecurrenceSeries, horizon_days: int = 180):
    """
    Matérialise les occurrences futures (jusqu'à horizon_days) pour une tâche récurrente.
    Idempotent grâce au couple (recurrence_series_id, scheduled_for) unique en base.
    """
    today = _today_utc_date()
    horizon_end = today + timedelta(days=horizon_days)

    # S'assurer que la tâche "template" est correctement attachée
    template_task.recurrence_series_id = series.id
    if template_task.scheduled_for is None:
        template_task.scheduled_for = series.start_date

    existing_dates = {
        d[0]
        for d in db.session.query(Task.scheduled_for)
        .filter(
            Task.recurrence_series_id == series.id,
            Task.scheduled_for.isnot(None),
            Task.scheduled_for <= horizon_end,
        )
        .all()
    }

    # Créer uniquement les occurrences >= aujourd'hui
    for d in series.iter_dates(horizon_end):
        if d < today:
            continue
        if d in existing_dates:
            continue
        cloned = template_task.clone_for_recurrence(scheduled_for=d, clone_checklist_items=True)
        db.session.add(cloned)


def _recurrence_payload(series: TaskRecurrenceSeries | None):
    if not series:
        return None
    return {
        "id": series.id,
        "frequency": series.frequency,
        "interval": series.interval,
        "start_date": series.start_date.isoformat(),
        "end_date": series.end_date.isoformat() if series.end_date else None,
        "count": series.count,
        "byweekday": series.byweekday,
        "business_days_only": bool(series.business_days_only),
    }


def _recurrence_summary_with_next(task: Task):
    series = task.recurrence_series
    if not series:
        return {"summary": "Aucune", "next_date": None}

    today = _today_utc_date()
    next_task = (
        Task.query.filter(
            Task.recurrence_series_id == series.id,
            Task.scheduled_for.isnot(None),
            Task.scheduled_for > today,
        )
        .order_by(Task.scheduled_for.asc())
        .first()
    )
    next_date = next_task.scheduled_for.strftime("%d/%m/%Y") if next_task else None

    summary = series.human_summary()
    if series.end_date:
        summary += f" (jusqu'au {series.end_date.strftime('%d/%m/%Y')})"
    elif series.count:
        summary += f" ({series.count} occurrence(s))"

    return {"summary": summary, "next_date": next_date}


tasks = Blueprint("tasks", __name__)


@tasks.route("/tasks")
@login_required
def list_tasks():
    """Liste toutes les tâches avec filtres et pagination"""
    # Récupération des paramètres de filtrage
    status = request.args.getlist("status")
    priority = request.args.get("priority")
    project_id = request.args.get("project_id", type=int)
    user_id = request.args.get("user_id", type=int)
    search = request.args.get("search")
    page = request.args.get("page", 1, type=int)
    per_page = 10

    # Construction de la requête de base
    query = Task.query

    # NOTE: on continue de masquer les tâches planifiées dans le futur sur la liste globale,
    # pour éviter du bruit. L'affichage "à venir" est géré sur les vues Kanban (projet / mes tâches).
    today = get_utc_now().date()
    query = query.filter(db.or_(Task.scheduled_for.is_(None), Task.scheduled_for <= today))

    # Filtres
    if status:
        query = query.filter(Task.status.in_(status))
    if priority:
        query = query.filter(Task.priority == priority)
    if project_id:
        query = query.filter(Task.project_id == project_id)
    if user_id:
        query = query.filter(Task.user_id == user_id)
    if search:
        query = query.filter(Task.title.ilike(f"%{search}%"))

    # Tri par défaut : date de création décroissante
    query = query.order_by(Task.created_at.desc())

    # Pagination
    tasks = query.paginate(page=page, per_page=per_page, error_out=False)

    # Récupération des données pour les filtres
    projects = Project.query.all()
    users = User.query.filter_by(role="technician").all()

    # Préparation des paramètres de requête pour la pagination
    query_params = {k: v for k, v in request.args.items() if k != "page"}

    return render_template("tasks/tasks.html", tasks=tasks, projects=projects, users=users, query_params=query_params)


@tasks.route("/projects/<slug_or_id>/tasks/new", methods=["GET", "POST"])
@login_and_client_required
def new_task(slug_or_id):
    project = get_project_by_slug_or_id(slug_or_id)
    form = TaskForm(current_user=current_user, project=project)

    if form.validate_on_submit():
        user_id = form.user_id.data if form.user_id.data != 0 else None

        # Convertir 0.0 (valeur pour "Non défini") à None
        estimated_time = None if form.estimated_time.data == 0.0 else form.estimated_time.data

        task = Task(
            title=form.title.data,
            description=form.description.data,
            status=form.status.data,
            priority=form.priority.data,
            estimated_time=estimated_time,
            project_id=project.id,
            user_id=user_id,
        )
        # Utiliser la méthode save() du modèle pour générer le slug
        task.save()

        # Optionnel: créer une récurrence dès la création
        recurrence_frequency = (request.form.get("recurrence_frequency") or "").strip()
        if recurrence_frequency and recurrence_frequency != "none":
            try:
                interval = int(request.form.get("recurrence_interval") or 1)
            except ValueError:
                interval = 1
            interval = max(1, min(interval, 365))

            start_date_raw = (request.form.get("recurrence_start_date") or "").strip()
            if start_date_raw:
                try:
                    start_date = datetime.strptime(start_date_raw, "%Y-%m-%d").date()
                except ValueError:
                    start_date = _today_utc_date()
            else:
                start_date = _today_utc_date()

            end_type = (request.form.get("recurrence_end_type") or "never").strip()
            end_date = None
            count = None
            if end_type == "until":
                end_date_raw = (request.form.get("recurrence_end_date") or "").strip()
                if end_date_raw:
                    try:
                        end_date = datetime.strptime(end_date_raw, "%Y-%m-%d").date()
                    except ValueError:
                        end_date = None
            elif end_type == "count":
                try:
                    count = int(request.form.get("recurrence_count") or 0)
                    if count <= 0:
                        count = None
                except ValueError:
                    count = None

            byweekday = None
            if recurrence_frequency == "weekly":
                days = request.form.getlist("recurrence_byweekday")
                days_int = []
                for d in days:
                    try:
                        di = int(d)
                    except ValueError:
                        continue
                    if 0 <= di <= 6:
                        days_int.append(di)
                byweekday = ",".join(str(d) for d in sorted(set(days_int))) or str(start_date.weekday())

            business_days_only = (request.form.get("recurrence_business_days_only") or "").strip().lower() in {
                "1",
                "true",
                "on",
                "yes",
            }

            series = TaskRecurrenceSeries(
                frequency=recurrence_frequency,
                interval=interval,
                start_date=start_date,
                end_date=end_date,
                count=count,
                byweekday=byweekday,
                business_days_only=business_days_only,
                template_task_id=task.id,
            )
            db.session.add(series)
            db.session.commit()

            task.recurrence_series_id = series.id
            task.scheduled_for = start_date
            _delete_future_recurrence_instances(series.id, keep_task_id=task.id)
            _ensure_recurrence_instances(task, series, horizon_days=180)
            db.session.commit()
            current_app.logger.info(f"Récurrence créée pour la tâche {task.id}: {series.frequency}")
        else:
            # Tâche non récurrente: pas de scheduled_for pour éviter de la masquer un jour
            task.scheduled_for = None
            db.session.commit()

        # Notifier l'assigné si la tâche est assignée
        if user_id:
            from app.utils.email import send_task_notification

            send_task_notification(
                task=task, event_type="task_created", user=current_user, additional_data=None, notify_all=True
            )

        flash(f'Tâche "{form.title.data}" créée avec succès!', "success")
        return redirect(url_for("projects.project_details", slug_or_id=project.slug))

    return render_template("tasks/task_form.html", form=form, project=project, title="Nouvelle tâche")


@tasks.route("/tasks/<slug_or_id>")
@login_required
def task_details(slug_or_id):
    task = get_task_by_slug_or_id(slug_or_id)

    # Vérifier si le client a accès à ce projet
    if current_user.is_client():
        project = task.project
        if not current_user.has_access_to_client(project.client_id):
            flash("Vous n'avez pas accès à cette tâche.", "danger")
            return redirect(url_for("main.dashboard"))

    time_entries = TimeEntry.query.filter_by(task_id=task.id).order_by(TimeEntry.created_at.desc()).all()

    # Récupérer les commentaires liés à cette tâche (sans les réponses)
    comments = Comment.query.filter_by(task_id=task.id, parent_id=None).order_by(Comment.created_at.desc()).all()

    # Formulaire pour ajouter du temps
    time_form = TimeEntryForm()

    # Formulaire pour ajouter un commentaire
    comment_form = CommentForm()

    # Formulaire pour éditer un commentaire
    edit_comment_form = EditCommentForm()

    # Formulaire pour la suppression
    delete_form = DeleteTaskForm()

    recurrence_info = _recurrence_summary_with_next(task)

    return render_template(
        "tasks/task_detail.html",
        task=task,
        time_entries=time_entries,
        comments=comments,
        time_form=time_form,
        comment_form=comment_form,
        edit_comment_form=edit_comment_form,
        form=delete_form,
        recurrence_info=recurrence_info,
        title=task.title,
    )


@tasks.route("/tasks/<slug_or_id>/recurrence", methods=["GET"])
@login_and_client_required
def get_task_recurrence(slug_or_id):
    task = get_task_by_slug_or_id(slug_or_id)
    info = _recurrence_summary_with_next(task)
    return jsonify(
        {
            "success": True,
            "has_recurrence": bool(task.recurrence_series),
            "recurrence": _recurrence_payload(task.recurrence_series),
            "summary": info["summary"],
            "next_date": info["next_date"],
        }
    )


@tasks.route("/tasks/<slug_or_id>/recurrence", methods=["POST"])
@login_and_client_required
def upsert_task_recurrence(slug_or_id):
    task = get_task_by_slug_or_id(slug_or_id)
    data = request.get_json(silent=True) or {}

    frequency = (data.get("frequency") or "").strip()
    if frequency not in {"daily", "weekly", "monthly"}:
        return jsonify({"success": False, "error": "Fréquence invalide"}), 400

    try:
        interval = int(data.get("interval") or 1)
    except (ValueError, TypeError):
        interval = 1
    interval = max(1, min(interval, 365))

    start_date_raw = (data.get("start_date") or "").strip()
    if start_date_raw:
        try:
            start_date = datetime.strptime(start_date_raw, "%Y-%m-%d").date()
        except ValueError:
            start_date = _today_utc_date()
    else:
        start_date = _today_utc_date()

    end_type = (data.get("end_type") or "never").strip()
    end_date = None
    count = None
    if end_type == "until":
        end_date_raw = (data.get("end_date") or "").strip()
        if end_date_raw:
            try:
                end_date = datetime.strptime(end_date_raw, "%Y-%m-%d").date()
            except ValueError:
                end_date = None
    elif end_type == "count":
        try:
            count = int(data.get("count") or 0)
            if count <= 0:
                count = None
        except (ValueError, TypeError):
            count = None

    byweekday = None
    if frequency == "weekly":
        days = data.get("byweekday") or []
        days_int = []
        for d in days:
            try:
                di = int(d)
            except (ValueError, TypeError):
                continue
            if 0 <= di <= 6:
                days_int.append(di)
        byweekday = ",".join(str(d) for d in sorted(set(days_int))) or str(start_date.weekday())

    business_days_only = bool(data.get("business_days_only")) if frequency == "daily" else False

    # Créer ou mettre à jour la série
    if task.recurrence_series:
        series = task.recurrence_series
        template_task = Task.query.get(series.template_task_id) or task
    else:
        series = TaskRecurrenceSeries(
            template_task_id=task.id, start_date=start_date, frequency=frequency, interval=interval
        )
        db.session.add(series)
        db.session.commit()
        task.recurrence_series_id = series.id
        template_task = task

    try:
        # Mettre à jour les paramètres
        series.frequency = frequency
        series.interval = interval
        series.start_date = start_date
        series.end_date = end_date
        series.count = count
        series.byweekday = byweekday
        series.business_days_only = business_days_only

        # Normaliser la tâche template
        task.recurrence_series_id = series.id
        template_task.recurrence_series_id = series.id
        template_task.scheduled_for = start_date

        # En cas de changement: supprimer/recréer les occurrences futures
        _delete_future_recurrence_instances(series.id, keep_task_id=template_task.id)
        _ensure_recurrence_instances(template_task, series, horizon_days=180)

        db.session.commit()
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Erreur upsert récurrence: {e}")
        return jsonify({"success": False, "error": "Erreur lors de la sauvegarde de la récurrence"}), 500

    info = _recurrence_summary_with_next(task)
    return jsonify(
        {
            "success": True,
            "message": "Récurrence enregistrée.",
            "has_recurrence": True,
            "recurrence": _recurrence_payload(task.recurrence_series),
            "summary": info["summary"],
            "next_date": info["next_date"],
        }
    )


@tasks.route("/tasks/<slug_or_id>/recurrence", methods=["DELETE"])
@login_and_client_required
def delete_task_recurrence(slug_or_id):
    task = get_task_by_slug_or_id(slug_or_id)
    series = task.recurrence_series
    if not series:
        return jsonify({"success": True, "message": "Aucune récurrence à supprimer."})

    try:
        # Supprimer les occurrences futures, puis détacher la série des tâches restantes
        _delete_future_recurrence_instances(series.id, keep_task_id=series.template_task_id)

        remaining_tasks = Task.query.filter(Task.recurrence_series_id == series.id).all()
        for t in remaining_tasks:
            t.recurrence_series_id = None
            # on ne garde scheduled_for que si déjà passé/aujourd'hui; sinon ça peut masquer
            if t.scheduled_for and t.scheduled_for > _today_utc_date():
                t.scheduled_for = None

        db.session.delete(series)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Erreur suppression récurrence: {e}")
        return jsonify({"success": False, "error": "Erreur lors de la suppression de la récurrence"}), 500

    return jsonify(
        {
            "success": True,
            "message": "Récurrence supprimée (occurrences futures supprimées).",
            "has_recurrence": False,
            "recurrence": None,
            "summary": "Aucune",
            "next_date": None,
        }
    )


@tasks.route("/tasks/<slug_or_id>/recurrence/checklist/sync", methods=["POST"])
@login_and_client_required
def sync_recurrence_checklist_to_future(slug_or_id):
    """
    Applique la checklist de la tâche "mère" (template_task_id) à toutes les occurrences futures:
    - uniquement occurrences futures (scheduled_for > aujourd'hui)
    - uniquement statut "à faire"
    - uniquement sans temps enregistré
    - merge additif: on ajoute les items manquants, sans supprimer ceux déjà présents.
    """
    task = get_task_by_slug_or_id(slug_or_id)
    series = task.recurrence_series
    if not series:
        return jsonify({"success": False, "error": "Aucune récurrence sur cette tâche."}), 400

    today = _today_utc_date()

    template_task = Task.query.get(series.template_task_id) or task

    # S'assurer que les occurrences futures existent (horizon glissant)
    try:
        _ensure_recurrence_instances(template_task, series, horizon_days=180)
        db.session.commit()
    except Exception:
        db.session.rollback()

    source_items = (
        ChecklistItem.query.filter(ChecklistItem.task_id == template_task.id)
        .order_by(ChecklistItem.position.asc())
        .all()
    )

    if not source_items:
        return jsonify({"success": True, "message": "Checklist de référence vide: rien à appliquer."})

    targets = Task.query.filter(
        Task.recurrence_series_id == series.id,
        Task.is_archived == False,
        Task.status == "à faire",
        Task.scheduled_for.isnot(None),
        Task.scheduled_for > today,
    ).all()

    updated_tasks = 0
    skipped_time_logged = 0
    added_items_total = 0

    for t in targets:
        # Sécurité: ne pas toucher aux occurrences sur lesquelles du temps a été enregistré
        if t.time_entries:
            skipped_time_logged += 1
            continue

        existing_items = (
            ChecklistItem.query.filter(ChecklistItem.task_id == t.id).order_by(ChecklistItem.position.asc()).all()
        )

        existing_contents = {(i.content or "").strip() for i in existing_items}
        max_pos = max([i.position for i in existing_items], default=-1)

        added_here = 0
        for src in source_items:
            content = (src.content or "").strip()
            if not content:
                continue
            if content in existing_contents:
                continue
            max_pos += 1
            db.session.add(ChecklistItem(content=content, is_checked=False, position=max_pos, task_id=t.id))
            existing_contents.add(content)
            added_here += 1

        if added_here:
            updated_tasks += 1
            added_items_total += added_here

    db.session.commit()

    if not targets:
        return jsonify({"success": True, "message": "Aucune occurrence future trouvée."})

    msg = f"Checklist appliquée: {added_items_total} élément(s) ajouté(s) sur {updated_tasks} occurrence(s) future(s)."
    if skipped_time_logged:
        msg += f" ({skipped_time_logged} occurrence(s) ignorée(s): temps déjà enregistré)"

    return jsonify(
        {
            "success": True,
            "message": msg,
            "updated_tasks": updated_tasks,
            "added_items_total": added_items_total,
            "skipped_time_logged": skipped_time_logged,
        }
    )


@tasks.route("/tasks/<slug_or_id>/edit", methods=["GET", "POST"])
@login_and_client_required
def edit_task(slug_or_id):
    from app.utils.email import send_task_notification

    task = get_task_by_slug_or_id(slug_or_id)

    # Vérifier si le client a accès à ce projet
    if current_user.is_client():
        project = task.project
        if not current_user.has_access_to_client(project.client_id):
            flash("Vous n'avez pas accès à cette tâche.", "danger")
            return redirect(url_for("main.dashboard"))

    # Initialiser le formulaire pour tous les utilisateurs
    form = TaskForm(current_user=current_user, project=task.project)

    if form.validate_on_submit():
        user_id = form.user_id.data if form.user_id.data != 0 else None

        # Capturer l'ancien statut avant modification
        old_status = task.status

        task.title = form.title.data
        task.description = form.description.data
        task.status = form.status.data
        task.priority = form.priority.data
        task.estimated_time = form.estimated_time.data
        task.user_id = user_id

        # Si la tâche est marquée comme terminée
        if task.status == "terminé" and not task.completed_at:
            # Convertir en datetime naive pour SQLite
            task.completed_at = get_utc_now().replace(tzinfo=None)
        elif task.status != "terminé":
            task.completed_at = None

        # Utiliser la méthode save() du modèle pour mettre à jour le slug
        task.save()

        # Envoyer une notification si le statut a changé
        if old_status != task.status:
            additional_data = {"old_status": old_status, "new_status": task.status}
            send_task_notification(
                task=task,
                event_type="status_change",
                user=current_user,
                additional_data=additional_data,
                notify_all=True,
            )

        flash(f'Tâche "{task.title}" mise à jour!', "success")
        return redirect(url_for("tasks.task_details", slug_or_id=task.slug))

    elif request.method == "GET":
        form.title.data = task.title
        form.description.data = task.description
        form.status.data = task.status
        form.priority.data = task.priority
        form.estimated_time.data = task.estimated_time
        form.user_id.data = task.user_id if task.user_id else 0

    return render_template("tasks/task_form.html", form=form, task=task, title="Modifier tâche")


@tasks.route("/tasks/<slug_or_id>/clone", methods=["POST"])
@login_and_client_required
def clone_task(slug_or_id):
    """Clone une tâche existante"""
    task = get_task_by_slug_or_id(slug_or_id)

    # Vérifier si le client a accès à ce projet
    if current_user.is_client():
        project = task.project
        if not current_user.has_access_to_client(project.client_id):
            flash("Vous n'avez pas accès à cette tâche.", "danger")
            return redirect(url_for("main.dashboard"))

    # Option : cloner (ou non) la checklist / sous-tâches.
    # Par défaut on clone, pour répondre au besoin #84.
    clone_checklist_raw = request.form.get("clone_checklist", "").strip().lower()
    clone_checklist = clone_checklist_raw not in {"0", "false", "off", "no"}

    # Créer une copie de la tâche
    cloned_task = task.clone(clone_checklist_items=clone_checklist)
    # Utiliser la méthode save() du modèle pour générer le slug
    cloned_task.save()

    flash(f'Tâche "{cloned_task.title}" créée avec succès!', "success")
    return redirect(url_for("tasks.task_details", slug_or_id=cloned_task.slug))


@tasks.route("/tasks/<slug_or_id>/delete", methods=["POST"])
@login_and_client_required
def delete_task(slug_or_id):
    task = get_task_by_slug_or_id(slug_or_id)
    project = task.project

    # Vérifier si le client a accès à ce projet et interdire la suppression pour les clients
    if current_user.is_client():
        flash("Accès refusé. Les clients ne peuvent pas supprimer de tâches.", "danger")
        return redirect(url_for("tasks.task_details", slug_or_id=task.slug))

    # Vérifier s'il y a du temps enregistré sur cette tâche
    if task.time_entries:
        flash("Impossible de supprimer cette tâche car du temps y a été enregistré.", "danger")
        return redirect(url_for("tasks.task_details", slug_or_id=task.slug))

    try:
        # Supprimer les relations qui n'ont pas de cascade delete
        # 1. Supprimer les UserPinnedTask liés à cette tâche
        UserPinnedTask.query.filter_by(task_id=task.id).delete()

        # 2. Mettre à NULL les task_id dans CreditLog (pour préserver l'historique)
        from app.models.project import CreditLog

        CreditLog.query.filter_by(task_id=task.id).update({"task_id": None})

        # 3. Mettre à NULL les task_id dans Communication (pour préserver l'historique)
        from app.models.communication import Communication

        Communication.query.filter_by(task_id=task.id).update({"task_id": None})

        # Maintenant on peut supprimer la tâche (toutes les opérations dans la même transaction)
        db.session.delete(task)
        db.session.commit()
        flash(f'Tâche "{task.title}" supprimée!', "success")
        return redirect(url_for("projects.project_details", slug_or_id=project.slug))
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Erreur lors de la suppression de la tâche: {str(e)}")
        flash(f"Erreur lors de la suppression de la tâche: {str(e)}", "danger")
        return redirect(url_for("tasks.task_details", slug_or_id=task.slug))


@tasks.route("/tasks/<slug_or_id>/log_time", methods=["POST"])
@login_required
def log_time(slug_or_id):
    from app.utils.email import send_task_notification

    task = get_task_by_slug_or_id(slug_or_id)

    # Vérifier si le client a accès à ce projet et interdire l'enregistrement de temps
    if current_user.is_client():
        if request.is_json or request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return jsonify(
                {"success": False, "error": "Accès refusé. Les clients ne peuvent pas enregistrer de temps."}
            ), 403
        flash("Accès refusé. Les clients ne peuvent pas enregistrer de temps.", "danger")
        return redirect(url_for("tasks.task_details", slug_or_id=task.slug))

    form = TimeEntryForm()

    if form.validate_on_submit():
        # Convertir le temps en minutes avec arrondi approprié
        time_in_minutes = round(form.hours.data * 60)

        # Créer l'entrée de temps
        time_entry = TimeEntry(
            task_id=task.id, user_id=current_user.id, minutes=time_in_minutes, description=form.description.data
        )
        db.session.add(time_entry)

        # Mettre à jour le temps total passé sur la tâche
        if task.actual_minutes is None:
            task.actual_minutes = time_in_minutes
        else:
            task.actual_minutes += time_in_minutes

        # Déduire du crédit du projet uniquement si la gestion de temps est activée
        if task.project.time_tracking_enabled:
            # Le crédit est toujours stocké en minutes dans la base de données
            task.project.remaining_credit -= time_in_minutes

        db.session.commit()

        # Envoyer une notification par email
        send_task_notification(task, "time_logged", current_user, {"time_entry": time_entry}, notify_all=True)

        # Formater le temps enregistré en heures et minutes
        hours = time_in_minutes // 60
        minutes = time_in_minutes % 60
        if hours > 0:
            time_display = f"{hours}h{minutes:02d}min"
        else:
            time_display = f"{minutes}min"
        success_message = f"{time_display} enregistrées sur la tâche!"

        # Si le crédit devient faible, afficher une alerte uniquement si la gestion de temps est activée
        warning_message = None
        if task.project.time_tracking_enabled:
            current_credit = task.project.remaining_credit
            if current_credit < 120:  # 2 heures en minutes
                remaining_hours = current_credit // 60
                remaining_minutes = current_credit % 60
                if remaining_hours > 0:
                    credit_display = f"{remaining_hours}h{remaining_minutes:02d}min"
                else:
                    credit_display = f"{remaining_minutes}min"
                warning_message = f"Attention: le crédit du projet est très bas ({credit_display})!"

        if request.is_json or request.headers.get("X-Requested-With") == "XMLHttpRequest":
            # Formater le temps restant pour l'affichage
            remaining_hours = task.project.remaining_credit // 60
            remaining_minutes = task.project.remaining_credit % 60
            if remaining_hours > 0:
                remaining_display = f"{remaining_hours}h{remaining_minutes:02d}min"
            else:
                remaining_display = f"{remaining_minutes}min"

            return jsonify(
                {
                    "success": True,
                    "message": success_message,
                    "warning": warning_message,
                    "time_entry": {
                        "id": time_entry.id,
                        "hours": time_entry.minutes / 60,  # Garder en décimal pour le calcul
                        "description": time_entry.description,
                        "created_at": time_entry.created_at.strftime("%d/%m %H:%M"),
                        "user_name": time_entry.user.name,
                    },
                    "task": {
                        "actual_time": task.actual_minutes / 60
                        if task.actual_minutes
                        else None,  # Garder en décimal pour le calcul
                        "remaining_credit": remaining_display
                        if task.project.time_tracking_enabled
                        else None,  # Afficher en format humain
                    },
                }
            )

        flash(success_message, "success")
        if warning_message:
            flash(warning_message, "warning")

    return redirect(url_for("tasks.task_details", slug_or_id=task.slug))


@tasks.route("/tasks/<slug_or_id>/time_entries", methods=["GET"])
@login_required
def get_time_entries(slug_or_id):
    task = get_task_by_slug_or_id(slug_or_id)
    time_entries = TimeEntry.query.filter_by(task_id=task.id).order_by(TimeEntry.created_at.desc()).all()

    return jsonify(
        {
            "success": True,
            "time_entries": [
                {
                    "id": entry.id,
                    "hours": entry.minutes / 60,  # Convertir les minutes en heures pour l'affichage
                    "description": entry.description,
                    "created_at": entry.created_at.strftime("%d/%m %H:%M"),
                    "user_name": entry.user.name,
                }
                for entry in time_entries
            ],
            "task": {
                "actual_time": task.actual_minutes / 60 if task.actual_minutes else None,  # Convertir en heures
                "remaining_credit": task.project.remaining_credit / 60
                if task.project.time_tracking_enabled
                else None,  # Convertir en heures
            },
        }
    )


@tasks.route("/tasks/update_status", methods=["POST"])
@login_required
def update_status():
    """Route pour mettre à jour le statut d'une tâche (via drag & drop du kanban)"""
    from app.utils.email import send_task_notification

    try:
        data = request.get_json()
        current_app.logger.info(f"Données reçues: {data}")

        task_id = data.get("task_id")
        new_status = data.get("status")

        if not task_id or not new_status:
            current_app.logger.error(f"Paramètres manquants: task_id={task_id}, status={new_status}")
            return jsonify({"success": False, "error": "Paramètres manquants"}), 400

        task = Task.query.get_or_404(task_id)

        # Vérifier les permissions
        if current_user.is_client():
            if not current_user.has_access_to_client(task.project.client_id):
                current_app.logger.error(
                    f"Accès non autorisé pour l'utilisateur {current_user.id} à la tâche {task_id}"
                )
                return jsonify({"success": False, "error": "Accès non autorisé"}), 403

        old_status = task.status
        task.status = new_status

        # Si la tâche est marquée comme terminée
        if new_status == "terminé" and not task.completed_at:
            task.completed_at = get_utc_now()
        elif new_status != "terminé":
            task.completed_at = None

        db.session.commit()

        # Envoyer une notification par email uniquement si le statut a changé
        if old_status != new_status:
            additional_data = {"old_status": old_status, "new_status": new_status}
            send_task_notification(
                task=task,
                event_type="status_change",
                user=current_user,
                additional_data=additional_data,
                notify_all=True,  # Activer les notifications pour tous les participants
            )

        current_app.logger.info(f"Statut de la tâche {task_id} mis à jour de '{old_status}' à '{new_status}'")

        return jsonify(
            {
                "success": True,
                "status": new_status,
                "completed_at": task.completed_at.strftime("%d/%m/%Y") if task.completed_at else None,
            }
        )
    except Exception as e:
        current_app.logger.error(f"Erreur lors de la mise à jour du statut: {str(e)}")
        db.session.rollback()
        return jsonify({"success": False, "error": str(e)}), 500


@tasks.route("/tasks/update_positions", methods=["POST"])
@login_required
def update_positions():
    """Route pour mettre à jour les positions des tâches dans une colonne"""
    try:
        data = request.get_json()
        task_positions = data.get("task_positions", [])

        if not task_positions:
            return jsonify({"success": False, "error": "Aucune position fournie"}), 400

        # Mettre à jour les positions
        for item in task_positions:
            task_id = item.get("task_id")
            position = item.get("position")

            if task_id and position is not None:
                task = Task.query.get(task_id)
                if task:
                    # Vérifier les permissions
                    if current_user.is_client():
                        if not current_user.has_access_to_client(task.project.client_id):
                            continue

                    task.position = position

        db.session.commit()
        return jsonify({"success": True})

    except Exception as e:
        current_app.logger.error(f"Erreur lors de la mise à jour des positions: {str(e)}")
        db.session.rollback()
        return jsonify({"success": False, "error": str(e)}), 500


@tasks.route("/my-tasks")
@login_required
def my_tasks():
    """Affiche les tâches assignées à l'utilisateur courant avec filtres"""
    # Récupération des paramètres de filtrage
    status = request.args.getlist("status")
    priority = request.args.get("priority")
    project_id = request.args.get("project_id", type=int)
    search = request.args.get("search")

    # Construction de la requête de base (exclure les tâches archivées)
    query = Task.query.filter_by(user_id=current_user.id, is_archived=False)
    today = get_utc_now().date()

    # Filtres
    if status:
        query = query.filter(Task.status.in_(status))
    if priority:
        query = query.filter(Task.priority == priority)
    if project_id:
        query = query.filter(Task.project_id == project_id)
    if search:
        query = query.filter(Task.title.ilike(f"%{search}%"))

    # On veut:
    # - toutes les tâches visibles (scheduled_for <= aujourd'hui)
    # - + uniquement la prochaine occurrence future par série (scheduled_for > aujourd'hui)
    #   pour pouvoir la montrer "à venir" dans À faire.

    visible_query = query.filter(db.or_(Task.scheduled_for.is_(None), Task.scheduled_for <= today))
    visible_query = visible_query.order_by(Task.position.asc(), Task.created_at.desc())
    all_tasks = visible_query.all()

    include_upcoming = (not status) or ("à faire" in status)
    if include_upcoming:
        # Sous-requête "prochaine date" par série
        next_subq = (
            db.session.query(
                Task.recurrence_series_id.label("sid"),
                func.min(Task.scheduled_for).label("next_date"),
            )
            .filter(
                Task.user_id == current_user.id,
                Task.is_archived == False,
                Task.recurrence_series_id.isnot(None),
                Task.scheduled_for.isnot(None),
                Task.scheduled_for > today,
                Task.status == "à faire",
            )
            .group_by(Task.recurrence_series_id)
            .subquery()
        )

        upcoming_next_q = db.session.query(Task).join(
            next_subq,
            db.and_(
                Task.recurrence_series_id == next_subq.c.sid,
                Task.scheduled_for == next_subq.c.next_date,
            ),
        )

        # Réappliquer les filtres optionnels (priority/project/search) sur la prochaine occurrence
        if priority:
            upcoming_next_q = upcoming_next_q.filter(Task.priority == priority)
        if project_id:
            upcoming_next_q = upcoming_next_q.filter(Task.project_id == project_id)
        if search:
            upcoming_next_q = upcoming_next_q.filter(Task.title.ilike(f"%{search}%"))

        upcoming_next_tasks = upcoming_next_q.all()
        all_tasks.extend(upcoming_next_tasks)

    # Tri des tâches par statut et par position
    def todo_sort_key(t: Task):
        if t.scheduled_for and t.scheduled_for > today:
            return (1, t.scheduled_for, t.created_at or datetime.min)
        return (0, t.position or 0, t.created_at or datetime.min)

    tasks_todo = sorted([task for task in all_tasks if task.status == "à faire"], key=todo_sort_key)
    tasks_in_progress = sorted(
        [task for task in all_tasks if task.status == "en cours"], key=lambda t: (t.position, t.created_at)
    )
    tasks_completed = sorted(
        [task for task in all_tasks if task.status == "terminé"],
        key=lambda t: (t.completed_at or t.created_at or datetime.min),
        reverse=True,
    )

    # Récupération des données pour les filtres
    projects = Project.query.all()

    # Préparation des paramètres de requête pour la pagination
    query_params = {k: v for k, v in request.args.items() if k != "page"}

    # Déterminer si des filtres sont actifs
    filters_active = bool(status or priority or project_id or search)

    return render_template(
        "tasks/my_tasks.html",
        tasks_todo=tasks_todo,
        tasks_in_progress=tasks_in_progress,
        tasks_completed=tasks_completed,
        projects=projects,
        query_params=query_params,
        filters_active=filters_active,
    )


@tasks.route("/archives")
@login_required
def archives():
    """Affiche les tâches archivées"""
    # Récupération des paramètres de filtrage
    project_id = request.args.get("project_id", type=int)
    search = request.args.get("search")
    page = request.args.get("page", 1, type=int)
    per_page = 20

    # Construction de la requête de base pour les tâches archivées
    query = Task.query.filter_by(is_archived=True)

    # Filtres
    if project_id:
        query = query.filter(Task.project_id == project_id)
    if search:
        query = query.filter(Task.title.ilike(f"%{search}%"))

    # Tri par date d'archivage décroissante
    query = query.order_by(Task.archived_at.desc())

    # Pagination
    archived_tasks = query.paginate(page=page, per_page=per_page, error_out=False)

    # Récupération des données pour les filtres
    projects = Project.query.all()

    # Récupération du projet spécifique si filtré
    current_project = None
    if project_id:
        current_project = Project.query.get(project_id)

    # Préparation des paramètres de requête pour la pagination
    query_params = {k: v for k, v in request.args.items() if k != "page"}

    return render_template(
        "tasks/archives.html",
        archived_tasks=archived_tasks,
        projects=projects,
        current_project=current_project,
        query_params=query_params,
    )


@tasks.route("/tasks/<slug_or_id>/archive", methods=["POST"])
@login_required
def archive_task(slug_or_id):
    """Archive une tâche"""
    task = get_task_by_slug_or_id(slug_or_id)

    # Vérifier les permissions
    if current_user.is_client():
        if not current_user.has_access_to_client(task.project.client_id):
            return jsonify({"success": False, "error": "Accès non autorisé"}), 403

    if task.status != "terminé":
        return jsonify({"success": False, "error": "Seules les tâches terminées peuvent être archivées"}), 400

    try:
        task.archive()
        return jsonify({"success": True, "message": f'La tâche "{task.title}" a été archivée'})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@tasks.route("/tasks/<slug_or_id>/unarchive", methods=["POST"])
@login_required
def unarchive_task(slug_or_id):
    """Désarchive une tâche"""
    task = get_task_by_slug_or_id(slug_or_id)

    # Vérifier les permissions
    if current_user.is_client():
        if not current_user.has_access_to_client(task.project.client_id):
            return jsonify({"success": False, "error": "Accès non autorisé"}), 403

    try:
        task.unarchive()
        return jsonify({"success": True, "message": f'La tâche "{task.title}" a été désarchivée'})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@tasks.route("/tasks/<slug_or_id>/add_comment", methods=["POST"])
@login_required
def add_comment(slug_or_id):
    from app.utils.email import send_task_notification

    task = get_task_by_slug_or_id(slug_or_id)

    # Vérifier si le client a accès à ce projet
    if current_user.is_client():
        project = task.project
        if not current_user.has_access_to_client(project.client_id):
            if request.is_json or request.headers.get("X-Requested-With") == "XMLHttpRequest":
                return jsonify({"success": False, "error": "Vous n'avez pas accès à cette tâche."}), 403
            flash("Vous n'avez pas accès à cette tâche.", "danger")
            return redirect(url_for("main.dashboard"))

    form = CommentForm()

    if form.validate_on_submit():
        # Récupérer les mentions depuis le champ caché
        mentioned_users = []
        try:
            mentions_data = request.form.get("mentions", "[]")
            mentioned_users = json.loads(mentions_data)
        except json.JSONDecodeError:
            current_app.logger.warning("Erreur lors du décodage des mentions")

        comment = Comment(content=form.content.data, task_id=task.id, user_id=current_user.id)
        save_to_db(comment)

        # Envoyer une notification en fonction des paramètres
        send_task_notification(
            task=task,
            event_type="comment_added",
            user=current_user,
            additional_data={"comment": comment},
            notify_all=form.notify_all.data,
            mentioned_users=mentioned_users,
        )

        if request.is_json or request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return jsonify(
                {
                    "success": True,
                    "message": "Votre commentaire a été ajouté.",
                    "comment": {
                        "id": comment.id,
                        "content": comment.content,
                        "created_at": comment.created_at.strftime("%d/%m/%Y %H:%M"),
                        "user_name": comment.user.name,
                        "user_id": comment.user.id,
                        "is_own_comment": comment.user_id == current_user.id,
                    },
                }
            )

        flash("Votre commentaire a été ajouté.", "success")
        return redirect(url_for("tasks.task_details", slug_or_id=slug_or_id))

    if request.is_json or request.headers.get("X-Requested-With") == "XMLHttpRequest":
        errors = {}
        for field, field_errors in form.errors.items():
            errors[field] = field_errors[0]
        return jsonify({"success": False, "errors": errors}), 400

    for field, errors in form.errors.items():
        for error in errors:
            flash(f"Erreur dans le champ {getattr(form, field).label.text} : {error}", "danger")

    return redirect(url_for("tasks.task_details", slug_or_id=slug_or_id))


@tasks.route("/tasks/comment/<int:comment_id>/delete", methods=["POST"])
@login_required
def delete_comment(comment_id):
    comment = Comment.query.get_or_404(comment_id)
    task = comment.task

    # Vérifier que l'utilisateur est l'auteur du commentaire ou un administrateur
    if comment.user_id != current_user.id and not current_user.is_admin():
        if request.is_json or request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return jsonify({"success": False, "error": "Vous n'êtes pas autorisé à supprimer ce commentaire."}), 403
        flash("Vous n'êtes pas autorisé à supprimer ce commentaire.", "danger")
        return redirect(url_for("tasks.task_details", slug_or_id=task.slug))

    delete_from_db(comment)

    if request.is_json or request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return jsonify({"success": True, "message": "Commentaire supprimé avec succès!"})

    flash("Commentaire supprimé avec succès!", "success")
    return redirect(url_for("tasks.task_details", slug_or_id=task.slug))


@tasks.route("/comments/<int:comment_id>/edit", methods=["POST"])
@login_required
def edit_comment(comment_id):
    """Route pour modifier un commentaire récent (moins de 10 minutes)"""
    comment = Comment.query.get_or_404(comment_id)
    task = comment.task
    form = EditCommentForm()

    # Vérifier que l'utilisateur est l'auteur du commentaire
    if comment.user_id != current_user.id and not current_user.is_admin():
        flash("Vous n'êtes pas autorisé à modifier ce commentaire.", "danger")
        return redirect(url_for("tasks.task_details", slug_or_id=task.slug))

    # Vérifier que le commentaire a moins de 10 minutes
    now = datetime.now(UTC)
    comment_time = comment.created_at.replace(tzinfo=UTC) if comment.created_at.tzinfo is None else comment.created_at
    delta = now - comment_time
    if delta.total_seconds() > 600:  # 10 minutes = 600 secondes
        flash("Ce commentaire ne peut plus être modifié (délai de 10 minutes dépassé).", "warning")
        return redirect(url_for("tasks.task_details", slug_or_id=task.slug))

    if form.validate_on_submit():
        # Mettre à jour le commentaire
        comment.content = form.content.data
        # Pas de mise à jour de created_at pour garder l'horodatage d'origine
        save_to_db(comment)

        if request.is_json or request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return jsonify(
                {
                    "success": True,
                    "message": "Commentaire modifié avec succès!",
                    "comment": {
                        "id": comment.id,
                        "content": comment.content,
                        "created_at": comment.created_at.strftime("%d/%m/%Y %H:%M"),
                        "user_name": comment.user.name,
                        "user_id": comment.user.id,
                        "is_own_comment": comment.user_id == current_user.id,
                        "parent_id": comment.parent_id,
                    },
                }
            )

        flash("Commentaire modifié avec succès !", "success")
    else:
        if request.is_json or request.headers.get("X-Requested-With") == "XMLHttpRequest":
            errors = {}
            for field, field_errors in form.errors.items():
                errors[field] = field_errors[0]
            return jsonify({"success": False, "errors": errors}), 400

        for field, errors in form.errors.items():
            for error in errors:
                flash(f"Erreur dans le champ {getattr(form, field).label.text}: {error}", "danger")

    return redirect(url_for("tasks.task_details", slug_or_id=task.slug))


@tasks.route("/tasks/<slug_or_id>/checklist", methods=["GET"])
@login_required
def get_checklist(slug_or_id):
    """Route pour récupérer la checklist complète d'une tâche"""
    task = get_task_by_slug_or_id(slug_or_id)

    # Vérifier si le client a accès à ce projet
    if current_user.is_client():
        if not current_user.has_access_to_client(task.project.client_id):
            return jsonify({"error": "Accès non autorisé"}), 403

    # Retourner la checklist complète
    all_checklist_items = (
        ChecklistItem.query.filter(ChecklistItem.task_id == task.id).order_by(ChecklistItem.position).all()
    )

    checklist = [
        {"id": item.id, "content": item.content, "is_checked": item.is_checked, "position": item.position}
        for item in all_checklist_items
    ]

    return jsonify({"success": True, "checklist": checklist})


@tasks.route("/tasks/<slug_or_id>/checklist", methods=["POST"])
@login_required
def add_checklist_item(slug_or_id):
    task = get_task_by_slug_or_id(slug_or_id)

    # Vérifier si le client a accès à ce projet
    if current_user.is_client():
        if not current_user.has_access_to_client(task.project.client_id):
            return jsonify({"error": "Accès non autorisé"}), 403

    data = request.get_json()

    if not data or "content" not in data:
        return jsonify({"error": "Contenu manquant"}), 400

    # Vérifier si c'est un shortcode
    if data.get("is_shortcode", False):
        if task.parse_checklist_shortcode(data["content"]):
            return jsonify({"success": True, "message": "Checklist créée avec succès"}), 201
        else:
            return jsonify({"error": "Format de shortcode invalide"}), 400

    # Sinon, ajouter un élément normal
    task.add_checklist_item(data["content"])

    # Retourner la checklist complète mise à jour, triée par position
    all_checklist_items = (
        ChecklistItem.query.filter(ChecklistItem.task_id == task.id).order_by(ChecklistItem.position).all()
    )

    checklist = [
        {"id": item.id, "content": item.content, "is_checked": item.is_checked, "position": item.position}
        for item in all_checklist_items
    ]

    return jsonify({"success": True, "checklist": checklist}), 201


@tasks.route("/tasks/<slug_or_id>/checklist/<int:item_id>", methods=["PUT"])
@login_required
def update_checklist_item(slug_or_id, item_id):
    try:
        task = get_task_by_slug_or_id(slug_or_id)

        # Vérifier si le client a accès à ce projet
        if current_user.is_client():
            if not current_user.has_access_to_client(task.project.client_id):
                return jsonify({"success": False, "error": "Accès non autorisé"}), 403

        item = ChecklistItem.query.get_or_404(item_id)

        # Vérifier que l'élément appartient bien à la tâche
        if item.task_id != task.id:
            return jsonify({"success": False, "error": "Élément non trouvé dans cette tâche"}), 404

        data = request.get_json()
        if not data:
            return jsonify({"success": False, "error": "Données JSON manquantes"}), 400

        if "is_checked" in data:
            item.is_checked = data["is_checked"]

        if "content" in data:
            item.content = data["content"]

        if "position" in data:
            item.position = data["position"]

        # Temporairement désactivé pour déboguer
        # Si l'élément vient d'être coché, le déplacer en bas automatiquement
        # if old_is_checked != new_is_checked and new_is_checked:
        #     # Logique de réorganisation temporairement désactivée
        #     pass

        db.session.commit()

        # Retourner la checklist complète mise à jour, triée par position
        # Récupérer tous les éléments de la tâche triés par position
        all_checklist_items = (
            ChecklistItem.query.filter(ChecklistItem.task_id == task.id).order_by(ChecklistItem.position).all()
        )

        checklist = [
            {"id": item.id, "content": item.content, "is_checked": item.is_checked, "position": item.position}
            for item in all_checklist_items
        ]

        return jsonify({"success": True, "checklist": checklist})

    except Exception as e:
        current_app.logger.error(f"Erreur lors de la mise à jour de l'élément de checklist: {str(e)}")
        current_app.logger.error(f"Type d'erreur: {type(e).__name__}")
        import traceback

        current_app.logger.error(f"Traceback: {traceback.format_exc()}")
        db.session.rollback()
        return jsonify({"success": False, "error": f"Erreur interne du serveur: {str(e)}"}), 500


@tasks.route("/tasks/<slug_or_id>/checklist/<int:item_id>", methods=["DELETE"])
@login_required
def delete_checklist_item(slug_or_id, item_id):
    task = get_task_by_slug_or_id(slug_or_id)

    # Vérifier si le client a accès à ce projet
    if current_user.is_client():
        if not current_user.has_access_to_client(task.project.client_id):
            return jsonify({"error": "Accès non autorisé"}), 403

    item = ChecklistItem.query.get_or_404(item_id)

    # Vérifier que l'élément appartient bien à la tâche
    if item.task_id != task.id:
        return jsonify({"error": "Élément non trouvé dans cette tâche"}), 404

    db.session.delete(item)
    db.session.commit()

    # Retourner la checklist complète mise à jour
    checklist = [
        {"id": item.id, "content": item.content, "is_checked": item.is_checked, "position": item.position}
        for item in task.checklist_items
    ]

    return jsonify({"success": True, "checklist": checklist})


@tasks.route("/tasks/<slug_or_id>/checklist/reorder", methods=["POST"])
@login_required
def reorder_checklist(slug_or_id):
    task = get_task_by_slug_or_id(slug_or_id)

    # Vérifier si le client a accès à ce projet
    if current_user.is_client():
        if not current_user.has_access_to_client(task.project.client_id):
            return jsonify({"error": "Accès non autorisé"}), 403

    data = request.get_json()

    if not data or "items" not in data:
        return jsonify({"error": "Données manquantes"}), 400

    # Valider que tous les éléments appartiennent à cette tâche
    item_ids = [item_data["id"] for item_data in data["items"]]
    existing_items = ChecklistItem.query.filter(ChecklistItem.id.in_(item_ids), ChecklistItem.task_id == task.id).all()

    if len(existing_items) != len(item_ids):
        return jsonify({"error": "Certains éléments ne sont pas valides"}), 400

    # Mettre à jour les positions et l'état des checkboxes
    for item_data in data["items"]:
        # S'assurer que l'ID est un entier
        item_id = int(item_data["id"]) if isinstance(item_data["id"], str) else item_data["id"]
        item = ChecklistItem.query.get(item_id)
        if item and item.task_id == task.id:
            item.position = item_data["position"]
            # Mettre à jour l'état de la checkbox si fourni (pour synchroniser avec le DOM)
            if "is_checked" in item_data:
                item.is_checked = bool(item_data["is_checked"])

    db.session.commit()

    # Retourner la checklist complète mise à jour
    all_checklist_items = (
        ChecklistItem.query.filter(ChecklistItem.task_id == task.id).order_by(ChecklistItem.position).all()
    )

    checklist = [
        {"id": item.id, "content": item.content, "is_checked": item.is_checked, "position": item.position}
        for item in all_checklist_items
    ]

    return jsonify({"success": True, "checklist": checklist})


@tasks.route("/comments/<int:comment_id>/reply", methods=["POST"])
@login_required
def add_reply(comment_id):
    """Ajoute une réponse à un commentaire"""
    from app.utils.email import send_task_notification

    parent_comment = Comment.query.get_or_404(comment_id)
    task = parent_comment.task

    # Vérifier si le client a accès à ce projet
    if current_user.is_client():
        if not current_user.has_access_to_client(task.project.client_id):
            if request.is_json or request.headers.get("X-Requested-With") == "XMLHttpRequest":
                return jsonify({"success": False, "error": "Vous n'avez pas accès à cette tâche."}), 403
            flash("Vous n'avez pas accès à cette tâche.", "danger")
            return redirect(url_for("main.dashboard"))

    form = CommentForm()

    if form.validate_on_submit():
        # Récupérer les mentions depuis le champ caché
        mentioned_users = []
        try:
            mentions_data = request.form.get("mentions", "[]")
            mentioned_users = json.loads(mentions_data)
        except json.JSONDecodeError:
            current_app.logger.warning("Erreur lors du décodage des mentions")

        reply = Comment(
            content=form.content.data, task_id=task.id, user_id=current_user.id, parent_id=parent_comment.id
        )
        save_to_db(reply)

        # Envoyer une notification à l'auteur du commentaire parent
        send_task_notification(
            task=task,
            event_type="comment_reply",
            user=current_user,
            additional_data={"reply": reply, "parent_comment": parent_comment},
            notify_all=False,  # Pour les réponses, on notifie seulement l'auteur du commentaire parent
            mentioned_users=mentioned_users,
        )

        if request.is_json or request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return jsonify(
                {
                    "success": True,
                    "message": "Réponse ajoutée avec succès!",
                    "comment": {
                        "id": reply.id,
                        "content": reply.content,
                        "created_at": reply.created_at.strftime("%d/%m/%Y %H:%M"),
                        "user_name": reply.user.name,
                        "user_id": reply.user.id,
                        "is_own_comment": reply.user_id == current_user.id,
                        "parent_id": reply.parent_id,
                    },
                }
            )

        flash("Réponse ajoutée avec succès!", "success")
    else:
        if request.is_json or request.headers.get("X-Requested-With") == "XMLHttpRequest":
            errors = {}
            for field, field_errors in form.errors.items():
                errors[field] = field_errors[0]
            return jsonify({"success": False, "errors": errors}), 400

        for field, errors in form.errors.items():
            for error in errors:
                flash(f"Erreur dans le champ {getattr(form, field).label.text}: {error}", "danger")

    return redirect(url_for("tasks.task_details", slug_or_id=task.slug))


@tasks.route("/task/<slug_or_id>/toggle_pin", methods=["POST"])
@login_required
def toggle_pin_task(slug_or_id):
    """Épingler ou désépingler une tâche pour l'utilisateur courant"""
    try:
        task = get_task_by_slug_or_id(slug_or_id)
        if not task:
            if request.is_json:
                return jsonify({"error": "Tâche non trouvée."}), 404
            flash("Tâche non trouvée.", "danger")
            return redirect(url_for("main.dashboard"))

        # Vérifier les permissions
        if current_user.is_client() and task.project.client not in current_user.clients:
            if request.is_json:
                return jsonify({"error": "Vous n'avez pas la permission d'effectuer cette action."}), 403
            flash("Vous n'avez pas la permission d'effectuer cette action.", "danger")
            return redirect(url_for("main.dashboard"))

        # Vérifier si la tâche est déjà épinglée
        is_pinned = task in current_user.pinned_tasks
        if is_pinned:
            # Désépingler
            UserPinnedTask.query.filter_by(user_id=current_user.id, task_id=task.id).delete()
            db.session.commit()
            if request.is_json:
                return jsonify(
                    {"success": True, "message": "La tâche a été désépinglée.", "is_pinned": False, "task_id": task.id}
                )
            flash("La tâche a été désépinglée.", "success")
        else:
            # Épingler
            new_pin = UserPinnedTask(user_id=current_user.id, task_id=task.id)
            db.session.add(new_pin)
            db.session.commit()
            if request.is_json:
                return jsonify(
                    {"success": True, "message": "La tâche a été épinglée.", "is_pinned": True, "task_id": task.id}
                )
            flash("La tâche a été épinglée.", "success")

        if request.is_json:
            return jsonify({"success": True})
        return redirect(request.referrer or url_for("tasks.task_details", slug_or_id=task.slug))
    except Exception as e:
        db.session.rollback()  # Annuler toute transaction en cours
        if request.is_json:
            return jsonify({"error": "Une erreur est survenue lors de l'opération.", "details": str(e)}), 500
        flash("Une erreur est survenue lors de l'opération.", "danger")
        return redirect(request.referrer or url_for("main.dashboard"))


@tasks.route("/api/tasks/<slug_or_id>/remaining-credit", methods=["GET"])
@login_required
def get_remaining_credit(slug_or_id):
    """Récupère le crédit restant d'une tâche"""
    task = get_task_by_slug_or_id(slug_or_id)

    # Vérifier si le client a accès à ce projet
    if current_user.is_client():
        project = task.project
        if not current_user.has_access_to_client(project.client_id):
            return jsonify({"error": "Accès non autorisé"}), 403

    # Le crédit est toujours stocké en minutes dans la base de données
    remaining_credit = task.project.remaining_credit
    if task.project.time_tracking_enabled and remaining_credit is not None:
        # Convertir en heures pour l'affichage
        remaining_credit = remaining_credit / 60

    return jsonify({"success": True, "remaining_credit": remaining_credit})
