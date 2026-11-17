# ABOUTME: Handlers for payment provider webhooks.
# ABOUTME: The provider retries and may deliver events late or out of order.
from depot.orders import now


def payment_succeeded(conn, order_id):
    conn.execute(
        "UPDATE orders SET status = 'paid', paid_at = ? WHERE id = ?",
        (now(), order_id),
    )
    conn.commit()


def refund_issued(conn, order_id):
    conn.execute(
        "UPDATE orders SET status = 'refunded', refunded_at = ? WHERE id = ?",
        (now(), order_id),
    )
    conn.commit()
