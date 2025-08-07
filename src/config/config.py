import os
from datetime import timedelta

from dotenv import load_dotenv

load_dotenv()

class Config:
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(minutes=30)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30)

    DB_HOST = os.getenv("DB_HOST")
    DB_PORT = os.getenv("DB_PORT")
    DB_NAME = os.getenv("DB_NAME")
    DB_USER = os.getenv("DB_USER")
    DB_PASS = os.getenv("DB_PASS")

    SQLALCHEMY_DATABASE_URI = (
        f"mysql+pymysql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Optimización de pool de conexiones DB
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_size': 20,           # Conexiones permanentes en el pool
        'max_overflow': 40,        # Conexiones adicionales si se necesitan
        'pool_timeout': 30,        # Timeout esperando una conexión libre
        'pool_recycle': 3600,      # Reciclar conexiones cada hora
        'pool_pre_ping': True,     # Validar conexiones antes de usar
        'echo': False              # No mostrar queries SQL (producción)
    }

    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    FIREBASE_CREDENTIALS_PATH = os.getenv("FIREBASE_CREDENTIALS_PATH")
    FIREBASE_STORAGE_BUCKET = os.getenv("FIREBASE_STORAGE_BUCKET")
    INTERNAL_SECRET_KEY = os.getenv("INTERNAL_SECRET_KEY")


