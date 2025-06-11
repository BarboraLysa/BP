from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from flask_bcrypt import Bcrypt

# Inicializácia objektu SQLAlchemy pre prácu s DB
db = SQLAlchemy()
# Inicializácia Bcrypt (na hashovanie hesiel)
bcrypt = Bcrypt()

class User(UserMixin, db.Model):
    # Model pre používateľa
    id = db.Column(db.Integer, primary_key=True) # Primárny kľúč
    name = db.Column(db.String(100), nullable=False) # Meno používateľa
    email = db.Column(db.String(100), unique=True, nullable=False) # E-mail, musí byť unikátny
    password = db.Column(db.String(255), nullable=False) # Zahashované heslo
    is_admin = db.Column(db.Boolean, default=False)  # True = admin, False = user

class Locker(db.Model):
    # Model pre schránku
    id = db.Column(db.Integer, primary_key=True) # Primárny kľúč
    code = db.Column(db.String(10), nullable=True)  # Kód pre odomknutie
    assigned_to = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=True)  # ID užívateľa, ktorému je schránka pridelená
    requested_by = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=True)  # ID užívateľa, ktorý požiadal o schránku
    is_active = db.Column(db.Boolean, default=False)  # Či je schránka obsadená

    # Vzťahy na model User: ak je schránka priradená konkrétnemu používateľovi
    assigned_user = db.relationship("User", foreign_keys=[assigned_to], backref="assigned_lockers", lazy=True)
    # Vzťah na model User: ak existuje požiadavka
    requested_user = db.relationship("User", foreign_keys=[requested_by], backref="requested_lockers", lazy=True)
