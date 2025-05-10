# ChronoTrak

<div align="center">

![Version](https://img.shields.io/badge/version-1.0.0-blue.svg?style=flat-square)
![Python](https://img.shields.io/badge/Python-3.11+-1F425F.svg?style=flat-square&logo=python&logoColor=white)
![Flask](https://img.shields.io/badge/Flask-3.1.0+-000000.svg?style=flat-square&logo=flask&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-Ready-2496ED.svg?style=flat-square&logo=docker&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green.svg?style=flat-square)

**Une solution open source de gestion de crédit-temps client**

*Simplifiez le suivi de vos prestations et la gestion de vos projets*

[Fonctionnalités](#-fonctionnalités) • 
[Installation](#-installation) • 
[Configuration](#-configuration) • 
[Sécurité](#-sécurité) • 
[Contribuer](#-contribuer) • 
[Licence](#-licence)

</div>

---

## 📋 Vue d'ensemble

**ChronoTrak** est une application web open sourc, développée à l'aide du framework Python `Flask`, qui part d'un besoin personnel en gestion de projet avec du crédit de temps pour des prestations diverses. 

Elle permet le suivi des heures allouées aux projets clients et une organisation des tâches en mode kanban.

## ✨ Fonctionnalités

### 🏢 Gestion des clients
- Création et modification des fiches clients
- Chiffrement des données sensibles (email, téléphone, adresse)
- Vue d'ensemble des projets par client
- Filtrage par nom, statut et date de création

### 📊 Gestion des projets
- Attribution d'un crédit d'heures initial par projet
- Suivi du solde d'heures restant
- Ajout de crédits supplémentaires
- Alertes lorsque le crédit devient faible
- Filtrage et tri des projets (nom, date, crédit)
- Correction manuelle du temps des tâches avec ajustement automatique du crédit

### 📝 Gestion des tâches
- Organisation des tâches en tableaux kanban (À faire, En cours, Terminé)
- Assignation des tâches aux utilisateurs
- Système de priorités (basse, normale, haute, urgente)
- Ajout de commentaires sur les tâches
- Modification des commentaires récents (délai de 10 minutes)
- Filtrage par statut, priorité, assignation et date
- Suivi automatique des dates de complétion
- Notifications par email lors des changements de statut

### ⏱️ Suivi du temps
- Enregistrement du temps passé sur chaque tâche
- Décompte automatique du crédit du projet
- Historique des temps passés
- Vue détaillée des temps récemment enregistrés
- Export des rapports de temps

### 🔐 Administration et sécurité
- Gestion des utilisateurs et des rôles (admin, technicien, client)
- Contrôle d'accès par client
- Notifications par email des événements importants
- Envoi automatique des informations d'accès aux nouveaux utilisateurs
- Système de réinitialisation de mot de passe sécurisé
- Chiffrement des données sensibles (clients et commentaires)

### 🎨 Interface utilisateur
- Design responsive adapté aux mobiles et ordinateurs
- Mode clair/sombre
- Tableau de bord avec indicateurs clés
- Système de cartes réduisables avec mémorisation des préférences
- Filtres dynamiques avec interface intuitive
- Notifications visuelles des actions réussies

## 🚀 Installation

### Via Docker (recommandé)

```bash
# Cloner le dépôt
git clone https://github.com/popallo/python-x-chronotrak
cd chronotrak

# Configuration environnement
cp .env.example .env.production
# Éditez le fichier .env.production avec vos paramètres

# Démarrage avec docker-compose
docker-compose up -d
```

### Installation manuelle

```bash
# Cloner le dépôt
git clone https://github.com/popallo/python-x-chronotrak
cd chronotrak

# Créer un environnement virtuel
python -m venv .venv
source .venv/bin/activate  # Sous Linux/macOS
# ou
.venv/bin/activate.ps1     # Sous Windows

# Installer les dépendances
pip install -r requirements.txt

# Configuration
cp .env.example .env
# Éditer le fichier .env selon votre environnement

# Initialiser la base de données
flask db upgrade

# Créer le compte administrateur
python scripts/create_admin.py

# Lancer l'application
flask run
```

## ⚙️ Configuration

ChronoTrak peut être configuré via plusieurs variables d'environnement :

| Variable            | Description                                            | Valeur par défaut         |
|---------------------|--------------------------------------------------------|---------------------------|
| `SECRET_KEY`        | Clé secrète pour sécuriser l'application              | Générée automatiquement   |
| `DATABASE_URL`      | URL de connexion à la base de données                 | SQLite (local)            |
| `ENCRYPTION_KEY`    | Clé pour le chiffrement des données sensibles         | Générée (⚠️ à sauvegarder) |
| `ADMIN_EMAIL`       | Email de l'administrateur initial                      | admin@example.com         |
| `ADMIN_PASSWORD`    | Mot de passe administrateur initial                    | changeme                  |
| `MAIL_SERVER`       | Serveur SMTP pour les notifications                    | localhost                 |
| `MAIL_PORT`         | Port du serveur SMTP                                   | 587                       |
| `MAIL_USERNAME`     | Nom d'utilisateur SMTP                                 | -                         |
| `MAIL_PASSWORD`     | Mot de passe SMTP                                      | -                         |
| `MAIL_USE_TLS`      | Utiliser TLS pour les emails                          | True                      |
| `MAIL_USE_SSL`      | Utiliser SSL pour les emails                          | False                     |
| `MAIL_DEFAULT_SENDER`| Adresse d'envoi par défaut                           | noreply@example.com       |
| `CREDIT_THRESHOLD`  | Seuil d'alerte pour le crédit bas (en heures)          | 2                         |
| `SESSION_LIFETIME`  | Durée de vie des sessions (en minutes)                | 120                       |
| `MAX_LOGIN_ATTEMPTS`| Nombre maximum de tentatives de connexion             | 5                         |
| `LOGIN_BLOCK_TIME`  | Durée de blocage après trop de tentatives (minutes)   | 15                        |
| `DEBUG`             | Mode debug (True/False)                               | False                     |
| `TESTING`           | Mode test (True/False)                                | False                     |

## 🔒 Sécurité

ChronoTrak intègre plusieurs mesures de sécurité :

- **Chiffrement des données** : Les informations sensibles des clients et les commentaires sont chiffrés
- **Authentification sécurisée** : Gestion des mots de passe avec bcrypt
- **Contrôle d'accès** : Isolation stricte des données entre clients
- **Protection contre les injections** : Utilisation de SQLAlchemy avec paramètres préparés

Pour plus d'informations, consultez notre [guide de sécurité](docs/security.md).

## 🛠️ Architecture technique

- **Backend** : Python avec Flask et extensions (Flask-SQLAlchemy, Flask-Login, Flask-WTF)
- **Base de données** : SQLite (développement), PostgreSQL/MySQL (production)
- **Frontend** : HTML5, CSS3, JavaScript avec Bootstrap 5
- **Containerisation** : Docker et docker-compose
- **Authentification** : Système à base de sessions avec Flask-Login
- **Chiffrement** : Bibliothèque cryptography avec Fernet

## 🔄 Contribuer

Les contributions sont les bienvenues ! Pour contribuer :

1. Forkez le projet
2. Créez une branche pour votre fonctionnalité (`git checkout -b feature/amazing-feature`)
3. Committez vos changements (`git commit -m 'Add some amazing feature'`)
4. Poussez vers la branche (`git push origin feature/amazing-feature`)
5. Ouvrez une Pull Request

## 📝 Licence

Ce projet est sous licence MIT - voir le fichier [LICENSE](LICENSE) pour plus de détails.

## 👥 Équipe

- **popallo** - Développeur principal - [@github](https://github.com/popallo)

---

<div align="center">
  <sub>Construit avec ❤️ par l'équipe ChronoTrak.</sub>
</div>