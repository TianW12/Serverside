# app/auth.py

from datetime import datetime, timedelta, timezone
from functools import wraps

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from apiflask import APIBlueprint
from flask import (
    current_app,
    jsonify,
    make_response,
    redirect,
    render_template,
    request,
    url_for,
)
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.database import get_session
from app.models import User


auth = APIBlueprint(
    "auth",
    __name__,
    url_prefix="/auth",
    tag="Authentication",
)

password_hasher = PasswordHasher()


def create_access_token(user_id):
    now = datetime.now(timezone.utc)

    payload = {
        "sub": str(user_id),
        "iat": now,
        "exp": now + timedelta(
            minutes=current_app.config["JWT_EXPIRATION_MINUTES"]
        ),
    }

    return jwt.encode(
        payload,
        current_app.config["JWT_SECRET"],
        algorithm=current_app.config["JWT_ALGORITHM"],
    )


def get_authenticated_user():
    token = request.cookies.get("access_token")

    if not token:
        return None

    try:
        payload = jwt.decode(
            token,
            current_app.config["JWT_SECRET"],
            algorithms=[
                current_app.config["JWT_ALGORITHM"]
            ],
        )

        user_id = int(payload["sub"])

    except (
        jwt.ExpiredSignatureError,
        jwt.InvalidTokenError,
        KeyError,
        TypeError,
        ValueError,
    ):
        return None

    with get_session() as session:
        user = session.get(
            User,
            user_id,
        )

        if user is None:
            return None

        return {
            "id": user.id,
            "username": user.username,
            "role": user.role,
            "created_at": user.created_at,
        }


def require_authentication(function):
    @wraps(function)
    def wrapper(*args, **kwargs):
        user = get_authenticated_user()

        if user is None:
            return jsonify({
                "error": "Authentication required"
            }), 401

        return function(
            *args,
            authenticated_user=user,
            **kwargs,
        )

    return wrapper


def require_admin(function):
    @wraps(function)
    def wrapper(*args, **kwargs):
        user = get_authenticated_user()

        if user is None:
            return redirect(
                url_for("admin.login")
            )

        if user["role"] != "admin":
            return jsonify({
                "error": "Administrator access required"
            }), 403

        return function(
            *args,
            authenticated_user=user,
            **kwargs,
        )

    return wrapper


@auth.get("/")
def auth_page():
    return render_template("auth/index.html")


@auth.get("/register")
def register_page():
    return render_template("auth/register.html")


@auth.post("/register")
def register():
    data = request.get_json(silent=True)

    if not data:
        return jsonify({
            "error": "JSON body required"
        }), 400

    username = data.get("username")
    password = data.get("password")

    if not isinstance(username, str) or not isinstance(password, str):
        return jsonify({
            "error": "Username and password are required"
        }), 400

    username = username.strip()

    if len(username) < 3 or len(username) > 100:
        return jsonify({
            "error": "Username must be between 3 and 100 characters"
        }), 400

    if len(password) < 12:
        return jsonify({
            "error": "Password must be at least 12 characters"
        }), 400

    password_hash = password_hasher.hash(password)

    with get_session() as session:
        user = User(
            username=username,
            password_hash=password_hash,
            role="user",
        )

        session.add(user)

        try:
            session.commit()

        except IntegrityError:
            session.rollback()

            return jsonify({
                "error": "User already exists"
            }), 409

        return jsonify({
            "message": "User registered successfully",
            "id": user.id,
            "username": user.username,
        }), 201


@auth.post("/login")
def login():
    data = request.get_json(silent=True)

    if not data:
        return jsonify({
            "error": "JSON body required"
        }), 400

    username = data.get("username")
    password = data.get("password")

    if not isinstance(username, str) or not isinstance(password, str):
        return jsonify({
            "error": "Username and password are required"
        }), 400

    username = username.strip()

    with get_session() as session:
        user = session.scalar(
            select(User)
            .where(User.username == username)
        )

        if user is None:
            return jsonify({
                "error": "User does not exist"
            }), 404

        try:
            password_hasher.verify(
                user.password_hash,
                password,
            )

        except VerifyMismatchError:
            return jsonify({
                "error": "Incorrect password"
            }), 401

        if password_hasher.check_needs_rehash(
            user.password_hash
        ):
            user.password_hash = password_hasher.hash(
                password
            )

            session.commit()

        token = create_access_token(user.id)

    response = make_response(
        jsonify({
            "message": "Login successful",
            "expires_in":
                current_app.config[
                    "JWT_EXPIRATION_MINUTES"
                ] * 60,
        })
    )

    response.set_cookie(
        "access_token",
        token,
        max_age=
            current_app.config[
                "JWT_EXPIRATION_MINUTES"
            ] * 60,
        httponly=True,
        secure=False,  # Change to True when serving over HTTPS
        samesite="Lax",
    )

    return response


@auth.post("/logout")
def logout():
    response = make_response(
        jsonify({
            "message": "Logged out"
        })
    )

    response.delete_cookie(
        "access_token",
        httponly=True,
        secure=False,  # Change to True when serving over HTTPS
        samesite="Lax",
    )

    return response


@auth.get("/me")
@require_authentication
def me(authenticated_user):
    return jsonify({
        "id": authenticated_user["id"],
        "username": authenticated_user["username"],
        "role": authenticated_user["role"],
        "created_at":
            authenticated_user["created_at"].isoformat(),
    })