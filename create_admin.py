from models import db, bcrypt, User
from server import app

with app.app_context():
    # Vytvor všetky tabuľky definované cez SQLAlchemy (ak ešte neexistujú)
    db.create_all()  
    # Skontroluj, či už existuje admin s e-mailom "admin@example.com"
    if not User.query.filter_by(email="admin@example.com").first(): 
        # Ak admin ešte neexistuje, vytvor ho: zahashuj heslo pomocou bcrypt
        password = bcrypt.generate_password_hash("adminpassword").decode("utf-8") 
        # Vytvor inštanciu používateľa s rolou admin (is_admin=True)
        admin = User(name="Admin", email="admin@example.com", password=password, is_admin=True) 
        # Pridaj do session a commitni, aby sa uložil do DB
        db.session.add(admin)
        db.session.commit()
        print("Admin bol vytvorený.")
    else:
        # Ak už admin existuje, vypíš
        print("Admin už existuje.")