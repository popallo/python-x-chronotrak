FROM python:3.11-alpine

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Créer un utilisateur non-root
RUN addgroup -S chronouser && adduser -S -G chronouser chronouser

# Installer Bash
RUN apk add --no-cache bash

# Créer le répertoire de l'application
WORKDIR /app

# Copier et installer les dépendances d'abord
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt && \
    python -m pip install gunicorn

RUN pip install pip-audit && \
    pip-audit && \
    pip install --upgrade setuptools>=70.0.0

# Copier uniquement les fichiers nécessaires
COPY app/ ./app/
COPY scripts/update_version.sh /app/scripts/update_version.sh
COPY migrations/ ./migrations/
COPY config.py run.py wsgi.py ./

# Créer le répertoire instance et définir les permissions
RUN mkdir -p /app/instance && \
    chown -R chronouser:chronouser /app && \
    chmod -R 755 /app && \
    chmod 777 /app/instance && \
    chmod +x /app/scripts/update_version.sh

# Passer à l'utilisateur non-root
USER chronouser

# Variable d'environnement par défaut pour Flask
ENV FLASK_APP=run.py \
    FLASK_ENV=production

EXPOSE 5000

CMD ["gunicorn", "--bind", "0.0.0.0:5000", "wsgi:app"]