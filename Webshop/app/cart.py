# app/cart.py

from decimal import Decimal
from apiflask import APIBlueprint
from flask import (
    Blueprint,
    jsonify,
    render_template,
    request,
    session as flask_session,
)
from sqlalchemy import select

from app.auth import require_authentication
from app.database import get_session
from app.inventory import check_reorder
from app.models import Article, Order, OrderLine


cart = APIBlueprint(
    "cart",
    __name__,
    url_prefix="/cart",
    tag="Cart",
)

def get_cart():
    return flask_session.setdefault("cart", {})


@cart.get("/")
def view_cart():
    cart_data = get_cart()

    items = []
    total = Decimal("0.00")

    with get_session() as session:
        for article_id, quantity in cart_data.items():
            article = session.get(
                Article,
                int(article_id),
            )

            if article is None:
                continue

            line_total = article.price * quantity

            items.append({
                "article": article,
                "quantity": quantity,
                "line_total": line_total,
            })

            total += line_total

    return render_template(
        "cart/index.html",
        items=items,
        total=total,
    )


@cart.post("/add")
def add_to_cart():
    data = request.get_json(silent=True)

    if not data:
        return jsonify({
            "error": "JSON body required"
        }), 400

    article_id = data.get("article_id")
    quantity = data.get("quantity", 1)

    if not isinstance(article_id, int):
        return jsonify({
            "error": "Invalid article"
        }), 400

    if not isinstance(quantity, int) or quantity < 1:
        return jsonify({
            "error": "Quantity must be at least 1"
        }), 400

    with get_session() as session:
        article = session.get(
            Article,
            article_id,
        )

        if article is None:
            return jsonify({
                "error": "Article not found"
            }), 404

        cart_data = get_cart()

        current_quantity = cart_data.get(
            str(article_id),
            0,
        )

        new_quantity = current_quantity + quantity

        if new_quantity > article.quantity_on_hand:
            return jsonify({
                "error": "Not enough stock available"
            }), 409

        cart_data[str(article_id)] = new_quantity

        flask_session.modified = True

    return jsonify({
        "message": "Added to cart"
    })


@cart.post("/update")
def update_cart():
    data = request.get_json(silent=True)

    if not data:
        return jsonify({
            "error": "JSON body required"
        }), 400

    article_id = data.get("article_id")
    quantity = data.get("quantity")

    if not isinstance(article_id, int):
        return jsonify({
            "error": "Invalid article"
        }), 400

    if not isinstance(quantity, int) or quantity < 0:
        return jsonify({
            "error": "Invalid quantity"
        }), 400

    cart_data = get_cart()

    if str(article_id) not in cart_data:
        return jsonify({
            "error": "Article is not in cart"
        }), 404

    if quantity == 0:
        del cart_data[str(article_id)]
        flask_session.modified = True

        return jsonify({
            "message": "Removed from cart"
        })

    with get_session() as session:
        article = session.get(
            Article,
            article_id,
        )

        if article is None:
            return jsonify({
                "error": "Article not found"
            }), 404

        if quantity > article.quantity_on_hand:
            return jsonify({
                "error": "Not enough stock available"
            }), 409

    cart_data[str(article_id)] = quantity
    flask_session.modified = True

    return jsonify({
        "message": "Cart updated"
    })


@cart.post("/checkout")
@require_authentication
def checkout(authenticated_user):
    cart_data = get_cart()

    if not cart_data:
        return jsonify({
            "error": "Cart is empty"
        }), 400

    with get_session() as session:
        try:
            order = Order(
                user_id=authenticated_user["id"],
                status="NEW",
                total_amount=Decimal("0.00"),
            )

            session.add(order)
            session.flush()

            total = Decimal("0.00")

            for article_id, quantity in cart_data.items():
                article = session.scalar(
                    select(Article)
                    .where(
                        Article.id == int(article_id)
                    )
                    .with_for_update()
                )

                if article is None:
                    session.rollback()

                    return jsonify({
                        "error":
                            f"Article {article_id} no longer exists"
                    }), 409

                if article.quantity_on_hand < quantity:
                    session.rollback()

                    return jsonify({
                        "error":
                            f"Not enough stock for {article.name}"
                    }), 409

                unit_price = article.price
                line_total = unit_price * quantity

                order_line = OrderLine(
                    order_id=order.id,
                    article_id=article.id,
                    quantity=quantity,
                    unit_price=unit_price,
                )

                session.add(order_line)

                article.quantity_on_hand -= quantity

                check_reorder(article)

                total += line_total

            order.total_amount = total

            session.commit()

        except Exception:
            session.rollback()
            raise

    flask_session["cart"] = {}
    flask_session.modified = True

    return jsonify({
        "message": "Order placed successfully",
        "order_id": order.id,
        "total_amount": str(order.total_amount),
    }), 201