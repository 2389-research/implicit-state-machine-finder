# ABOUTME: Web checkout flow. The session dict carries the customer's progress between requests.
# ABOUTME: Steps in order: cart, address, payment, confirm.
from depot.orders import create_order


def start(session, cart_total_cents):
    session["cart_total_cents"] = cart_total_cents
    session["step"] = "address"


def submit_address(session, address):
    session["address"] = address
    session["step"] = "payment"


def submit_payment(session, payment_token):
    session["payment_token"] = payment_token
    session["step"] = "confirm"


def confirm(conn, session):
    if not session.get("payment_token"):
        raise ValueError("no payment method")
    order_id = create_order(conn, session["cart_total_cents"])
    session["order_id"] = order_id
    return order_id


def current_page(session):
    return {
        None: "cart.html",
        "address": "address.html",
        "payment": "payment.html",
        "confirm": "confirm.html",
    }[session.get("step")]
