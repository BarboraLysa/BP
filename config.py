import os

class Config:
    SECRET_KEY = os.urandom(24)  # Zabezpečenie relácií
    SQLALCHEMY_DATABASE_URI = "sqlite:///database.db"  # SQLite databáza
    SQLALCHEMY_TRACK_MODIFICATIONS = False