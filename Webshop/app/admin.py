# app/admin.py
from apiflask import APIBlueprint
from flask import Blueprint, render_template
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.auth import require_admin
from app.database import get_session
from app.models import (
    Article,
    GoodsReceived,
    Order,
    OrderLine,
    User,
)

admin = APIBlueprint(
    "admin",
    __name__,
    url_prefix="/admin",
    tag="Admin",
)

@admin.get("/login")
def login():
    return render_template("admin/login.html")


@admin.get("/")
@require_admin
def dashboard(authenticated_user):
    with get_session() as session:
        user_count = len(
            session.scalars(
                select(User)
            ).all()
        )

        order_count = len(
            session.scalars(
                select(Order)
            ).all()
        )

        article_count = len(
            session.scalars(
                select(Article)
            ).all()
        )

    return render_template(
        "admin/index.html",
        user_count=user_count,
        order_count=order_count,
        article_count=article_count,
        authenticated_user=authenticated_user,
    )


@admin.get("/users")
@require_admin
def users(authenticated_user):
    with get_session() as session:
        users = session.scalars(
            select(User)
            .order_by(User.created_at.desc())
        ).all()

    return render_template(
        "admin/users.html",
        users=users,
        authenticated_user=authenticated_user,
    )


@admin.get("/orders")
@require_admin
def orders(authenticated_user):
    with get_session() as session:
        orders = session.scalars(
            select(Order)
            .options(
                selectinload(Order.user)
            )
            .order_by(Order.order_date.desc())
        ).all()

    return render_template(
        "admin/orders.html",
        orders=orders,
        authenticated_user=authenticated_user,
    )


@admin.get("/orders/<int:order_id>")
@require_admin
def order_detail(
    order_id,
    authenticated_user,
):
    with get_session() as session:
        order = session.scalar(
            select(Order)
            .where(
                Order.id == order_id
            )
            .options(
                selectinload(Order.user),
                selectinload(Order.lines)
                .selectinload(OrderLine.article),
            )
        )

        if order is None:
            return "Order not found", 404

    return render_template(
        "admin/order_detail.html",
        order=order,
        authenticated_user=authenticated_user,
    )


@admin.get("/inventory")
@require_admin
def inventory(authenticated_user):
    with get_session() as session:
        articles = session.scalars(
            select(Article)
            .order_by(Article.name)
        ).all()

    return render_template(
        "admin/inventory.html",
        articles=articles,
        authenticated_user=authenticated_user,
    )


@admin.get("/goods-received")
@require_admin
def goods_received(authenticated_user):
    with get_session() as session:
        goods_received = session.scalars(
            select(GoodsReceived)
            .options(
                selectinload(
                    GoodsReceived.article
                )
            )
            .order_by(
                GoodsReceived.received_at.desc()
            )
        ).all()

    return render_template(
        "admin/goods_received.html",
        goods_received=goods_received,
        authenticated_user=authenticated_user,
    )