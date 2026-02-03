# scripts/initialize_notification_prefs.py
from app import create_app, db
from app.models.notification import NotificationPreference
from app.models.user import User

app = create_app("development")

with app.app_context():
    users = User.query.all()
    count = 0

    for user in users:
        if not user.notification_preferences:
            preference = NotificationPreference(user_id=user.id)
            db.session.add(preference)
            count += 1

    if count > 0:
        db.session.commit()
        print(f"Préférences de notification créées pour {count} utilisateurs")
    else:
        print("Aucune préférence de notification à initialiser")
