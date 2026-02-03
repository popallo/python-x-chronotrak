from app import create_app, db
from app.models.user import User

app = create_app("development")

with app.app_context():
    # Vérifier si l'admin existe déjà
    admin_email = app.config.get("ADMIN_EMAIL")
    if not User.query.filter_by(email=admin_email).first():
        admin = User(email=admin_email, name="Admin", role="admin")
        admin.set_password(app.config.get("ADMIN_PASSWORD"))
        db.session.add(admin)
        db.session.commit()
        print(f"Utilisateur admin créé avec l'email: {admin_email}")
    else:
        print(f"Un utilisateur admin avec l'email {admin_email} existe déjà.")
