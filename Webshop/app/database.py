# app/database.py

from flask import current_app
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


engine = None
SessionLocal = None


def init_database(app):
    global engine
    global SessionLocal

    engine = create_engine(
        app.config["DATABASE_URL"],
        pool_pre_ping=True,
    )

    SessionLocal = sessionmaker(
        bind=engine,
        expire_on_commit=False,
    )


def get_session():
    return SessionLocal()
