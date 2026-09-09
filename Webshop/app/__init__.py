# app/__init__.py

from apiflask import APIFlask

from app.admin import admin
from app.auth import auth
from app.cart import cart
from app.config import Config
from app.database import init_database
from app.shop import shop


def create_app():
    app = APIFlask(
        __name__,
        title="Shop API",
        version="1.0.0",
    )

    app.config.from_object(Config)

    app.secret_key = app.config["FLASK_SECRET"]

    init_database(app)

    app.register_blueprint(auth)
    app.register_blueprint(cart)
    app.register_blueprint(admin)
    app.register_blueprint(shop)

    return app