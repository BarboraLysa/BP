from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from flask_bcrypt import Bcrypt

db = SQLAlchemy()
bcrypt = Bcrypt()

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)  # True = admin, False = user

class Locker(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(10), nullable=True)  # Kód pre odomknutie
    assigned_to = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=True)  # ID užívateľa, ktorému je schránka pridelená
    requested_by = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=True)  # ID užívateľa, ktorý požiadal o schránku
    is_active = db.Column(db.Boolean, default=False)  # Či je schránka obsadená

    assigned_user = db.relationship("User", foreign_keys=[assigned_to], backref="assigned_lockers", lazy=True)
    requested_user = db.relationship("User", foreign_keys=[requested_by], backref="requested_lockers", lazy=True)
