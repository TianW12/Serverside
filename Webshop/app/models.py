# app/models.py

from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    username: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        nullable=False,
    )

    password_hash: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    role: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="user",
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.current_timestamp(),
    )

    orders: Mapped[list["Order"]] = relationship(
        back_populates="user",
    )


class Article(Base):
    __tablename__ = "articles"

    __table_args__ = (
        CheckConstraint(
            "price >= 0",
            name="articles_price_check",
        ),
        CheckConstraint(
            "quantity_on_hand >= 0",
            name="articles_quantity_on_hand_check",
        ),
        CheckConstraint(
            "reorder_point >= 0",
            name="articles_reorder_point_check",
        ),
        CheckConstraint(
            "reorder_quantity > 0",
            name="articles_reorder_quantity_check",
        ),
    )

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    article_number: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        nullable=False,
    )

    name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    price: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        nullable=False,
    )

    quantity_on_hand: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    reorder_point: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=5,
    )

    reorder_quantity: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=10,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.current_timestamp(),
    )

    order_lines: Mapped[list["OrderLine"]] = relationship(
        back_populates="article",
    )

    goods_received: Mapped[list["GoodsReceived"]] = relationship(
        back_populates="article",
    )


class Order(Base):
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False,
    )

    order_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.current_timestamp(),
    )

    status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="NEW",
    )

    total_amount: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
        default=0,
    )

    user: Mapped["User"] = relationship(
        back_populates="orders",
    )

    lines: Mapped[list["OrderLine"]] = relationship(
        back_populates="order",
        cascade="all, delete-orphan",
    )


class OrderLine(Base):
    __tablename__ = "order_lines"

    __table_args__ = (
        CheckConstraint(
            "quantity > 0",
            name="order_lines_quantity_check",
        ),
        CheckConstraint(
            "unit_price >= 0",
            name="order_lines_unit_price_check",
        ),
    )

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    order_id: Mapped[int] = mapped_column(
        ForeignKey(
            "orders.id",
            ondelete="CASCADE",
        ),
        nullable=False,
    )

    article_id: Mapped[int] = mapped_column(
        ForeignKey("articles.id"),
        nullable=False,
    )

    quantity: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    unit_price: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        nullable=False,
    )

    order: Mapped["Order"] = relationship(
        back_populates="lines",
    )

    article: Mapped["Article"] = relationship(
        back_populates="order_lines",
    )


class GoodsReceived(Base):
    __tablename__ = "goods_received"

    __table_args__ = (
        CheckConstraint(
            "quantity > 0",
            name="goods_received_quantity_check",
        ),
    )

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    article_id: Mapped[int] = mapped_column(
        ForeignKey("articles.id"),
        nullable=False,
    )

    quantity: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    received_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.current_timestamp(),
    )

    reference: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    article: Mapped["Article"] = relationship(
        back_populates="goods_received",
    )