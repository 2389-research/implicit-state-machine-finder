# ABOUTME: Warehouse shipping pass, run every ten minutes.
# ABOUTME: Ships every order that has been paid for and has not left yet.
from depot.orders import now


def ship_ready_orders(conn):
    rows = conn.execute(
        "SELECT id FROM orders WHERE paid_at IS NOT NULL AND shipped_at IS NULL"
    ).fetchall()
    shipped = []
    for row in rows:
        conn.execute(
            "UPDATE orders SET status = 'shipped', shipped_at = ? WHERE id = ?",
            (now(), row["id"]),
        )
        shipped.append(row["id"])
    conn.commit()
    return shipped
