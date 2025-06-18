# Règles d'envoi d'emails - ChronoTrak

## Vue d'ensemble

Ce document décrit les règles d'envoi d'emails implémentées dans ChronoTrak pour assurer une communication appropriée selon l'environnement (développement vs production).

## Règles générales

### Environnement de développement/local

**Règle :** Tous les emails sont redirigés vers les administrateurs uniquement.

- **Comportement :** Peu importe les destinataires initiaux, tous les emails sont envoyés aux administrateurs
- **Identification :** Le sujet est préfixé avec `[DEV]` ou `[LOCAL]` et contient les destinataires initiaux
- **Exemple :** `[DEV] Notification de tâche (pour client@example.com, admin@example.com)`

### Environnement de production

**Règle 1 :** Les administrateurs reçoivent tous les emails en copie, sauf s'ils sont les seuls destinataires initiaux.

- **Comportement :** Si l'email est destiné à des non-administrateurs, les administrateurs sont automatiquement ajoutés en copie
- **Exception :** Si l'email est destiné uniquement aux administrateurs, aucun destinataire supplémentaire n'est ajouté

**Règle 2 :** Pour les emails liés à un projet, le client responsable du projet reçoit automatiquement l'email.

- **Comportement :** Si l'email est lié à un projet (via `project_id`), les utilisateurs clients ayant accès à ce projet reçoivent l'email
- **Préférences :** Les préférences de notification du client sont respectées
- **Types concernés :** 
  - `task_status_change` : Changements de statut des tâches
  - `task_comment_added` : Nouveaux commentaires
  - `task_time_logged` : Enregistrement de temps
  - `project_low_credit` : Alerte de crédit faible

## Types d'emails

### 1. Notifications de tâches

**Fonction :** `send_task_notification()`

**Types d'événements :**
- `status_change` : Changement de statut d'une tâche
- `comment_added` : Ajout d'un commentaire
- `time_logged` : Enregistrement de temps

**Destinataires en production :**
- Utilisateur assigné à la tâche (selon ses préférences)
- Clients du projet (selon leurs préférences)
- Administrateurs (en copie)
- Utilisateurs mentionnés dans les commentaires

### 2. Alertes de crédit faible

**Fonction :** `send_low_credit_notification()`

**Destinataires en production :**
- Administrateurs (selon leurs préférences)
- Clients du projet (selon leurs préférences)

### 3. Réinitialisation de mot de passe

**Fonction :** `send_password_reset_email()`

**Destinataires :**
- Utilisateur concerné
- Administrateurs (en copie en production)

### 4. Emails de test

**Fonction :** `send_test_email()`

**Destinataires :**
- Destinataire spécifié
- Administrateurs (en copie en production)

### 5. Emails d'erreur

**Fonction :** `send_error_email()`

**Destinataires :**
- Administrateurs uniquement

## Implémentation technique

### Fonction centrale : `send_email()`

Toute la logique de détermination des destinataires est centralisée dans la fonction `send_email()` du module `app/utils/email.py`.

**Paramètres importants :**
- `recipients` : Liste des destinataires initiaux
- `email_type` : Type d'email pour appliquer les bonnes règles
- `project_id` : ID du projet lié (pour les règles clients)
- `user_id` : ID de l'utilisateur concerné
- `task_id` : ID de la tâche concernée

### Vérification de l'environnement

L'environnement est déterminé par la variable `FLASK_ENV` :
- `development` ou `local` : Règles de développement
- `production` : Règles de production

### Gestion des préférences

Les préférences de notification sont vérifiées via le modèle `NotificationPreference` :
- `email_notifications_enabled` : Activation générale
- `task_status_change` : Changements de statut
- `task_comment_added` : Nouveaux commentaires
- `task_time_logged` : Enregistrement de temps
- `project_credit_low` : Alertes de crédit

## Tests et vérification

### Scripts de test

1. **`scripts/test_email_rules.py`** : Test des règles d'envoi
2. **`scripts/check_communications.py`** : Vérification des communications envoyées

### Vérification de conformité

```bash
# Vérifier les communications récentes
python scripts/check_communications.py --hours 24

# Vérifier la conformité aux règles
python scripts/check_communications.py --compliance
```

### Test des règles

```bash
# Tester les règles d'envoi
python scripts/test_email_rules.py
```

## Logs et monitoring

### Logs d'application

Les actions d'envoi d'emails sont loggées avec les informations suivantes :
- Redirection vers les administrateurs en dev
- Ajout d'administrateurs en copie en prod
- Ajout de clients aux destinataires
- Échecs d'envoi

### Table des communications

Toutes les communications sont enregistrées dans la table `Communication` avec :
- Destinataire
- Sujet
- Contenu (chiffré)
- Type d'email
- Statut (sent/failed)
- Références (user_id, task_id, project_id)

## Configuration

### Variables d'environnement

- `FLASK_ENV` : Environnement (development/production)
- `ADMIN_EMAIL` : Email administrateur principal
- `MAIL_SERVER` : Serveur SMTP
- `MAIL_USERNAME` : Nom d'utilisateur SMTP
- `MAIL_PASSWORD` : Mot de passe SMTP

### Configuration des préférences

Les utilisateurs peuvent configurer leurs préférences de notification via leur profil :
- Activation/désactivation des notifications
- Types de notifications souhaités
- Fréquence des notifications

## Dépannage

### Problèmes courants

1. **Emails non reçus en production**
   - Vérifier la configuration SMTP
   - Vérifier les préférences de notification
   - Consulter les logs d'application

2. **Administrateurs non en copie**
   - Vérifier que les administrateurs ont un email valide
   - Vérifier que l'environnement est bien en production

3. **Clients non notifiés**
   - Vérifier les préférences de notification du client
   - Vérifier l'accès du client au projet
   - Vérifier que le projet_id est bien passé

### Commandes utiles

```bash
# Vérifier la configuration SMTP
python -c "from app import create_app; app = create_app(); print(app.config.get('MAIL_SERVER'))"

# Tester l'envoi d'email
curl -X POST http://localhost:5000/admin/test-email -d "recipient=test@example.com"

# Vérifier les communications récentes
python scripts/check_communications.py --hours 1
``` 