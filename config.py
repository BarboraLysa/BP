import os

class Config:
    SECRET_KEY = os.urandom(24)   # Generovanie náhodného tajného kľúča pre zabezpečenie relácií
    SQLALCHEMY_DATABASE_URI = "sqlite:///database.db"  # Nastavenie URI pre SQLite databázu
    SQLALCHEMY_TRACK_MODIFICATIONS = False # Vypnutie sledovania zmien