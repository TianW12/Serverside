# app/config.py

import os

from dotenv import load_dotenv


load_dotenv()


class Config:
    DATABASE_URL = os.getenv("DATABASE_URL")

    JWT_SECRET = os.getenv("JWT_SECRET")
    JWT_ALGORITHM = "HS256"
    JWT_EXPIRATION_MINUTES = 15

    FLASK_SECRET = os.getenv("FLASK_SECRET")