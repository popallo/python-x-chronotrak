# Guide d'implémentation du chiffrement des données dans ChronoTrak

Ce guide détaille les étapes pour ajouter le chiffrement des données sensibles dans l'application ChronoTrak.

## Principe de fonctionnement

Le chiffrement est implémenté au niveau des modèles SQLAlchemy pour les données sensibles comme les coordonnées clients (email, téléphone, adresse) et les notes. Cela permet de chiffrer automatiquement les données avant leur stockage en base et de les déchiffrer lors de leur lecture.

Nous utilisons la bibliothèque `cryptography` avec l'algorithme Fernet qui fournit un chiffrement symétrique sécurisé.

## Prérequis

1. Installer les dépendances nécessaires:
   ```bash
   # Avec uv (recommandé)
   uv add cryptography

   # Ou avec pip
   pip install cryptography
   ```

2. Générer une clé de chiffrement:
   ```bash
   python -c "import base64; import os; print(base64.urlsafe_b64encode(os.urandom(32)).decode('utf-8'))"
   ```

3. Ajouter cette clé dans votre fichier `.env`:
   ```
   ENCRYPTION_KEY=votre_clé_générée
   ```

## Étapes d'implémentation

### 1. Préparation de l'environnement

1. **Sauvegardez votre base de données actuelle**:
   ```bash
   cp instance/chronotrak.db instance/chronotrak.db.backup
   ```

2. **Ajoutez la clé de chiffrement à votre environnement**:
   - Créez ou modifiez votre fichier `.env` pour inclure `ENCRYPTION_KEY`
   - Pour la production, assurez-vous de sauvegarder cette clé dans un endroit sûr

### 2. Migration de la base de données

1. **Exécutez la migration Alembic** pour modifier les colonnes:
   ```bash
   flask db upgrade
   ```

   Cela va augmenter la taille des colonnes pour qu'elles puissent contenir les données chiffrées.

### 3. Chiffrement des données existantes

1. **Exécutez le script de chiffrement**:
   ```bash
   python encrypt_existing_data.py
   ```

   Ce script va:
   - Vérifier la présence de la clé de chiffrement
   - Parcourir tous les clients dans la base de données
   - Chiffrer les données sensibles qui ne sont pas encore chiffrées
   - Enregistrer les modifications dans la base de données

### 4. Vérification

Après avoir exécuté ces étapes, vérifiez que tout fonctionne correctement:

1. **Lancez l'application**:
   ```bash
   flask run
   ```

2. **Vérifiez que vous pouvez toujours accéder aux données clients**:
   - Connectez-vous à l'application
   - Consultez les détails des clients
   - Les données devraient être affichées normalement (déchiffrées automatiquement)

3. **Vérifiez le chiffrement en base de données**:
   ```bash
   sqlite3 instance/chronotrak.db
   sqlite> SELECT email, phone FROM client LIMIT 3;
   ```
   Les données devraient apparaître chiffrées.

## Remarques importantes

1. **Sauvegarde de la clé**:
   - Si vous perdez la clé de chiffrement, vous perdrez l'accès à toutes les données chiffrées
   - Utilisez un gestionnaire de secrets ou une solution sécurisée pour stocker cette clé

2. **Recherche dans les données chiffrées**:
   - Il n'est pas possible d'effectuer des recherches SQL directes sur les champs chiffrés
   - Si vous avez besoin de rechercher par email ou téléphone, il faudra implémenter une recherche côté application

3. **Rotation des clés**:
   - Si vous devez changer la clé de chiffrement, vous devrez déchiffrer toutes les données avec l'ancienne clé et les rechiffrer avec la nouvelle
   - Un script spécifique devra être développé pour cette opération

## Dépannage

1. **Erreurs de déchiffrement**:
   - Si vous voyez des erreurs indiquant que les données ne peuvent pas être déchiffrées, vérifiez que vous utilisez la bonne clé
   - Vérifiez que les données sont bien au format attendu par Fernet

2. **Performances**:
   - Le chiffrement/déchiffrement ajoute une légère surcharge
   - Si les performances sont un problème, envisagez de limiter le chiffrement aux données les plus sensibles

3. **Taille des données**:
   - Les données chiffrées sont plus volumineuses que les données en clair
   - Si des erreurs surviennent à cause de la taille, augmentez la longueur maximale des colonnes dans la migration

## Expansion future

Ce système de chiffrement peut être étendu à d'autres modèles si nécessaire:

1. Descriptions des projets sensibles
2. Informations confidentielles dans les tâches
3. Notes et commentaires privés

Pour chaque ajout, suivez le même processus:
1. Modifiez le modèle pour utiliser `EncryptedType`
2. Créez une migration pour ajuster la taille des colonnes
3. Écrivez un script pour chiffrer les données existantes
