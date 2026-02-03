"""
Tests unitaires pour le modèle Project.
"""
import pytest
from app import db
from app.models.project import Project, CreditLog


def test_project_creation(app, test_project):
    """Test la création d'un projet."""
    with app.app_context():
        # S'assurer que le projet est attaché à la session
        project = db.session.merge(test_project)
        assert project.id is not None
        assert project.name == 'Projet Test'
        assert project.initial_credit == 600
        assert project.remaining_credit == 600
        assert project.time_tracking_enabled is True


def test_project_slug_generation(app, test_client):
    """Test la génération automatique de slug."""
    with app.app_context():
        # S'assurer que le client est attaché à la session
        client = db.session.merge(test_client)
        # Utiliser un nom unique pour éviter les conflits
        project = Project(name='Mon Super Projet Unique', client_id=client.id)
        db.session.add(project)
        db.session.commit()
        
        assert project.slug == 'mon-super-projet-unique'
        assert project.slug is not None


def test_project_add_credit(app, test_project):
    """Test l'ajout de crédit au projet."""
    with app.app_context():
        # S'assurer que le projet est attaché à la session
        project = db.session.merge(test_project)
        initial_credit = project.remaining_credit
        
        # Ajouter 2 heures de crédit
        project.add_credit(2.0, note='Ajout de crédit test')
        db.session.commit()
        db.session.refresh(project)
        
        # Vérifier que le crédit a été ajouté (2h = 120 minutes)
        assert project.remaining_credit == initial_credit + 120
        
        # Vérifier qu'un log a été créé
        log = CreditLog.query.filter_by(project_id=project.id).order_by(CreditLog.id.desc()).first()
        assert log is not None
        assert log.amount == 120
        assert 'Ajout de crédit test' in log.note


def test_project_add_credit_conversion(app, test_project):
    """Test la conversion heures -> minutes lors de l'ajout."""
    with app.app_context():
        # S'assurer que le projet est attaché à la session
        project = db.session.merge(test_project)
        initial_credit = project.remaining_credit
        
        # Ajouter 1.5 heures (90 minutes)
        project.add_credit(1.5)
        db.session.commit()
        db.session.refresh(project)
        
        assert project.remaining_credit == initial_credit + 90


def test_project_deduct_credit(app, test_project):
    """Test la déduction de crédit du projet."""
    with app.app_context():
        # S'assurer que le projet est attaché à la session
        project = db.session.merge(test_project)
        initial_credit = project.remaining_credit
        
        # Déduire 1 heure de crédit
        project.deduct_credit(1.0, note='Déduction de crédit test')
        db.session.commit()
        db.session.refresh(project)
        
        # Vérifier que le crédit a été déduit (1h = 60 minutes)
        assert project.remaining_credit == initial_credit - 60
        
        # Vérifier qu'un log a été créé avec montant négatif
        log = CreditLog.query.filter_by(project_id=project.id).order_by(CreditLog.id.desc()).first()
        assert log is not None
        assert log.amount == -60
        assert 'Déduction de crédit test' in log.note


def test_project_deduct_credit_alert_threshold(app, test_client):
    """Test que l'alerte est déclenchée quand le crédit passe sous le seuil."""
    with app.app_context():
        # S'assurer que le client est attaché à la session
        client = db.session.merge(test_client)
        
        # Créer un projet avec 3 heures de crédit (180 minutes)
        project = Project(
            name='Projet Test Alert',
            client_id=client.id,
            initial_credit=180,
            remaining_credit=180,
            time_tracking_enabled=True
        )
        db.session.add(project)
        db.session.commit()
        
        assert project.credit_alert_sent is False
        
        # Déduire 2 heures (120 minutes) pour passer sous le seuil de 2h
        project.deduct_credit(2.0)
        db.session.commit()
        db.session.refresh(project)
        
        # Le crédit restant est 60 minutes (< 120 minutes = seuil)
        assert project.remaining_credit == 60
        assert project.credit_alert_sent is True


def test_project_add_credit_resets_alert(app, test_client):
    """Test que l'ajout de crédit réinitialise l'alerte si le crédit redevient suffisant."""
    with app.app_context():
        # S'assurer que le client est attaché à la session
        client = db.session.merge(test_client)
        
        # Créer un projet avec crédit faible
        project = Project(
            name='Projet Test Reset',
            client_id=client.id,
            initial_credit=60,  # 1 heure (< seuil de 2h)
            remaining_credit=60,
            time_tracking_enabled=True,
            credit_alert_sent=True  # Alerte déjà envoyée
        )
        db.session.add(project)
        db.session.commit()
        
        assert project.credit_alert_sent is True
        
        # Ajouter 2 heures pour passer au-dessus du seuil
        project.add_credit(2.0)
        db.session.commit()
        db.session.refresh(project)
        
        # Le crédit est maintenant 180 minutes (>= 120 minutes = seuil)
        assert project.remaining_credit == 180
        assert project.credit_alert_sent is False


def test_project_no_credit_operations_when_time_tracking_disabled(app, test_client):
    """Test que les opérations de crédit ne font rien si time_tracking_enabled est False."""
    with app.app_context():
        # S'assurer que le client est attaché à la session
        client = db.session.merge(test_client)
        
        project = Project(
            name='Projet Sans Tracking',
            client_id=client.id,
            initial_credit=600,
            remaining_credit=600,
            time_tracking_enabled=False
        )
        db.session.add(project)
        db.session.commit()
        
        initial_credit = project.remaining_credit
        
        # Essayer d'ajouter du crédit
        project.add_credit(2.0)
        db.session.commit()
        db.session.refresh(project)
        
        # Le crédit ne doit pas avoir changé
        assert project.remaining_credit == initial_credit
        
        # Essayer de déduire du crédit
        project.deduct_credit(1.0)
        db.session.commit()
        db.session.refresh(project)
        
        # Le crédit ne doit toujours pas avoir changé
        assert project.remaining_credit == initial_credit


def test_project_add_credit_no_log_if_no_id(app, test_client):
    """Test qu'aucun log n'est créé si le projet n'a pas encore d'ID."""
    with app.app_context():
        # S'assurer que le client est attaché à la session
        client = db.session.merge(test_client)
        
        project = Project(
            name='Projet Nouveau',
            client_id=client.id,
            initial_credit=0,
            remaining_credit=0,
            time_tracking_enabled=True
        )
        # Ne pas encore ajouter à la session
        
        # Ajouter du crédit avant que le projet soit sauvegardé
        project.add_credit(1.0)
        
        # Le crédit doit être mis à jour localement
        assert project.remaining_credit == 60
        
        # Mais aucun log ne doit exister car le projet n'a pas d'ID
        db.session.add(project)
        db.session.commit()
        
        # Maintenant vérifier qu'aucun log n'a été créé avant le commit
        logs_before = CreditLog.query.filter_by(project_id=project.id).count()
        assert logs_before == 0


def test_project_repr(app, test_project):
    """Test la représentation string d'un projet."""
    with app.app_context():
        # S'assurer que le projet est attaché à la session
        project = db.session.merge(test_project)
        repr_str = repr(project)
        assert 'Projet Test' in repr_str
        assert 'Client' in repr_str
        assert '600min' in repr_str
