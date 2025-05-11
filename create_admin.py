from models import db, bcrypt, User
from server import app

with app.app_context():
    db.create_all()
    if not User.query.filter_by(email="admin@example.com").first():
        password = bcrypt.generate_password_hash("adminpassword").decode("utf-8")
        admin = User(name="Admin", email="admin@example.com", password=password, is_admin=True)
        db.session.add(admin)
        db.session.commit()
        print("Admin bol vytvorený.")
    else:
        print("Admin už existuje.")