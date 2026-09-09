# app/shop.py

from apiflask import APIBlueprint
from flask import render_template
from sqlalchemy import select

from app.database import get_session
from app.models import Article

shop = APIBlueprint(
    "shop",
    __name__,
    tag="Shop",
)
@shop.get("/")
def index():
    with get_session() as session:
        articles = session.scalars(
            select(Article)
            .where(Article.quantity_on_hand > 0)
            .order_by(Article.name)
        ).all()

    return render_template(
        "shop/index.html",
        articles=articles,
    )


@shop.get("/articles/<int:article_id>")
def article(article_id):
    with get_session() as session:
        article = session.get(
            Article,
            article_id,
        )

    if article is None:
        return "Article not found", 404

    return render_template(
        "shop/article.html",
        article=article,
    )
