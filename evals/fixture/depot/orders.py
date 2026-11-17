# ABOUTME: Order creation and customer-initiated changes.
# ABOUTME: Payment and refund events arrive through webhooks.py; shipping through fulfilment.py.
from datetime import datetime, timezone


def now():
    return datetime.now(timezone.utc).isoformat()


def create_order(conn, total_cents):
    cur = conn.execute("INSERT INTO orders (total_cents) VALUES (?)", (total_cents,))
    conn.commit()
    return cur.lastrowid


def get_order(conn, order_id):
    return conn.execute("SELECT * FROM orders WHERE id = ?", (order_id,)).fetchone()


def cancel_order(conn, order_id):
    order = get_order(conn, order_id)
    if order["shipped_at"]:
        raise ValueError("order already shipped")
    conn.execute(
        "UPDATE orders SET status = 'cancelled', cancelled_at = ? WHERE id = ?",
        (now(), order_id),
    )
    conn.commit()
