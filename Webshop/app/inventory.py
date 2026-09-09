# app/inventory.py

from sqlalchemy import select
from sqlalchemy.orm import object_session

from app.database import get_session
from app.models import Article, GoodsReceived


def place_reorder(article):
    session = object_session(article)

    if session is None:
        raise RuntimeError(
            "Article must belong to an active database session"
        )

    quantity = article.reorder_quantity

    goods_received = GoodsReceived(
        article_id=article.id,
        quantity=quantity,
        reference="AUTOMATIC REORDER",
    )

    session.add(goods_received)

    article.quantity_on_hand += quantity

    reorder = {
        "article_id": article.id,
        "article_number": article.article_number,
        "name": article.name,
        "quantity": quantity,
        "goods_received": goods_received,
    }

    print(
        f"Reorder executed: "
        f"{reorder['article_number']} - "
        f"{reorder['quantity']} units"
    )

    return reorder


def check_reorder(article):
    if article.quantity_on_hand > article.reorder_point:
        return None

    return place_reorder(article)


def check_all_reorders():
    with get_session() as session:
        articles = session.scalars(
            select(Article)
            .where(
                Article.quantity_on_hand
                <= Article.reorder_point
            )
            .order_by(Article.name)
        ).all()

        reorders = [
            place_reorder(article)
            for article in articles
        ]

        session.commit()

        return reorders